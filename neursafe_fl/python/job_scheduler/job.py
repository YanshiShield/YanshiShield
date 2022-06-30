#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint: disable = too-few-public-methods, too-many-instance-attributes
# pylint:disable=too-many-arguments, broad-except
"""
"""
from copy import deepcopy
import os
import re
import time
import shutil

from absl import logging
from tornado import gen
from tornado.ioloop import IOLoop

from neursafe_fl.proto.job_stop_service_grpc import JobStopServiceStub
from neursafe_fl.proto.select_service_grpc import SelectServiceStub
from neursafe_fl.proto.message_pb2 import ClientRequirement
from neursafe_fl.proto.message_pb2 import Metadata
from neursafe_fl.python.job_scheduler.coordinator import Coordinator
import neursafe_fl.python.job_scheduler.util.const as const
import neursafe_fl.python.job_scheduler.util.errors as errors
from neursafe_fl.python.job_scheduler.util.model_client import ModelClient
from neursafe_fl.python.job_scheduler.util.operation_retry import \
    route_operation_retry, coordinator_operation_retry
from neursafe_fl.python.trans.grpc_call import unary_call
from neursafe_fl.python.trans.proxy import Proxy, ProxyError


MAX_TRY_DELETE_CKPT = 3


class State:
    """Define state"""

    QUEUING = "QUEUING"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    FAILED = "FAILED"
    DELETING = "DELETING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    PENDING = "PENDING"

    ALL_STATES = [QUEUING, STARTING, RUNNING, FINISHED,
                  FAILED, DELETING, STOPPING, STOPPED,
                  PENDING]


class Operation:
    """Define operations"""

    START = "START"
    DELETE = "DELETE"
    STOP = "STOP"
    UPDATE = "UPDATE"


class JobStatus:
    """
    Fl job statues class
    """

    def __init__(self):
        self.state = State.QUEUING
        self.reason = None
        self.progress = 0

    def update(self, status):
        """
        Update job status

        Args:
            status: fl job status info.
        """
        for key, value in status.items():
            setattr(self, key, value)

    def to_dict(self):
        """
        Convert fl job status object to dict.

        Returns:
            fl job status info in dict type.
        """
        return {"state": self.state,
                "reason": self.reason,
                "progress": self.progress}


class Job:
    """
    Federated learning job class
    """
    def __init__(self, namespace, job_config, callbacks):
        self.__job_config = job_config

        self.__id = job_config["id"]
        self.__namespace = namespace

        self.__status = JobStatus()
        if "status" in job_config:
            self.__status.update(job_config["status"])

        self.__create_time = job_config.get("time",
                                            time.strftime("%Y-%m-%d %H:%M:%S",
                                                          time.localtime()))
        self.__start_time = job_config.get("start_time", self.__create_time)
        self.__checkpoints = job_config.get("checkpoints", {})

        self.__db_callback = callbacks["db_callback"]
        self.__delete_callback = callbacks["delete_callback"]
        self.__finish_callback = callbacks["finish_callback"]

        self.__heartbeat_timer = None
        self.__coordinator = Coordinator()
        self.__route_register = Proxy()

        self.__first_heartbeat_received = False
        self.__starting_process_stopped = False

    def assert_operation_valid(self, operation):
        """
        Assert operation whether valid according to current job state

        Args:
            operation: operation, such as:START, STOP, DELETE and so on.

        Raises:
             JobSchedulerError
        """
        state = self.__status.state

        supported_operations = {
            State.RUNNING: [Operation.DELETE, Operation.STOP],
            State.STARTING: [Operation.DELETE, Operation.STOP],
            State.PENDING: [Operation.DELETE, Operation.STOP, Operation.UPDATE],
            State.FAILED: [Operation.DELETE, Operation.UPDATE, Operation.START,
                           Operation.STOP],
            State.QUEUING: [Operation.DELETE, Operation.STOP, Operation.UPDATE],
            State.FINISHED: [Operation.DELETE, Operation.START,
                             Operation.UPDATE],
            State.DELETING: [],
            State.STOPPING: [Operation.DELETE],
            State.STOPPED: [Operation.DELETE, Operation.START, Operation.UPDATE]
        }

        if operation not in supported_operations[state]:
            raise errors.JobSchedulerError(
                "Namespace: %s, job id: %s in state: %s, can not do "
                "operation: %s." % (self.__namespace,
                                    self.__id,
                                    state,
                                    operation))

    def __do_create_successfully(self):
        if self.__status.state in [State.RUNNING, State.STARTING]:
            state = State.RUNNING
            self.__update_status({"state": state})
            logging.info("start heartbeat: namespace: %s, job id: %s"
                         % (self.__namespace, self.__id))
            self.__refresh_heart_timer()

            logging.info("Namespace: %s, job id: %s, "
                         "create coordinator successfully.", self.__namespace,
                         self.__id)

    @gen.coroutine
    def __do_run_failed(self):
        state = State.FAILED
        reason = "Coordinator run failed."
        self.__update_status({"state": state,
                              "reason": reason})

        logging.error("Namespace: %s, job id: %s, "
                      "coordinator run failed.", self.__namespace,
                      self.__id)
        self.__finish_callback(self.__namespace,
                               self.__id)

    @coordinator_operation_retry
    @gen.coroutine
    def __do_create_coordinator(self):
        if self.__status.state is State.STARTING:
            try:
                # TODO: workspace related to data object store
                yield self.__coordinator.create(
                    self.__gen_coordinator_cfg(),
                    workspace=os.path.join(const.WORKSPACE,
                                           const.TEMP_DIR),
                    namespace=self.__namespace)
                logging.info("Request create namespace: %s, jod id: %s "
                             "coordinator successfully.", self.__namespace,
                             self.__id)
            except errors.CoordinatorExists:
                logging.error("Namespace: %s, job id: %s, coordinator already "
                              "exists, recreate coordinator",
                              self.__namespace,
                              self.__id)
                yield self.__do_delete_coordinator()
                yield self.__do_create_coordinator()
        else:
            logging.warning("Namespace: %s, job id: %s current state: %s, no"
                            "need to create coordinator", self.__namespace,
                            self.__id, self.__status.state)

    @coordinator_operation_retry
    @gen.coroutine
    def __do_delete_coordinator(self):
        try:
            yield self.__coordinator.delete(self.__id,
                                            self.__namespace)
            logging.info("Request delete namespace: %s, jod id: %s, "
                         "coordinator successfully.", self.__namespace,
                         self.__id)
            yield self.__wait_coordinator_deleted()
        except errors.CoordinatorNotExist:
            logging.info("Namespace: %s, job id: %s, "
                         "coordinator already deleted",
                         self.__namespace,
                         self.__id)

    @coordinator_operation_retry
    @gen.coroutine
    def __get_coordinator_status(self):
        status = yield self.__coordinator.status(self.__id,
                                                 self.__namespace)

        raise gen.Return(status)

    @route_operation_retry
    @gen.coroutine
    def __do_create_proxy_route(self):
        if self.__status.state in State.STARTING:
            service_address = "%s-%s" % (self.__namespace, self.__id)
            port = self.__job_config["port"]
            yield self.__route_register.add(self.__namespace,
                                            self.__id,
                                            "%s:%s" % (service_address, port))
            logging.info("Create proxy route successfully for namespace: %s, "
                         "job id: %s", self.__namespace, self.__id)
        else:
            logging.warning("Namespace: %s, job id: %s current state: %s, no"
                            "need to create proxy route", self.__namespace,
                            self.__id, self.__status.state)

    @gen.coroutine
    def __do_delete_proxy_route(self):
        try:
            yield self.__route_register.delete(self.__namespace,
                                               self.__id)
            logging.info("Delete proxy route successfully for namespace: %s, "
                         "job id: %s", self.__namespace, self.__id)
        except ProxyError as error:
            logging.warning("Delete route for namespace: %s, job id: %s, "
                            "error info: %s" % (self.__namespace,
                                                self.__id,
                                                str(error)))

    @gen.coroutine
    def __wait_coordinator_running(self):
        while True:
            try:
                status = yield self.__get_coordinator_status()
                logging.info("Namespace: %s, job id: %s coordinator state: %s "
                             "in waiting to running process.",
                             self.__namespace, self.__id, status)
            except errors.CoordinatorNotExist:
                logging.warning(
                    "Coordinator of Namespace: %s, job id: %s not exist, "
                    "waiting running"
                    % (self.__namespace, self.__id))
                yield gen.sleep(const.RETRY_INTERVAL)
                continue
            finally:
                if self.__status.state != State.STARTING:
                    logging.info("Namespace: %s job id: %s in state: %s, "
                                 "coordinator no need to wait running.",
                                 self.__namespace, self.__id,
                                 self.__status.state)
                    self.__starting_process_stopped = True
                    return  # pylint:disable=lost-exception

            if self.__first_heartbeat_received:
                # if receive first heartbeat, it means coordinator
                # is running
                logging.info(
                    "Coordinator of Namespace: %s, job id: %s RUNNING."
                    % (self.__namespace, self.__id))
                self.__do_create_successfully()
                break

            if status["state"] == State.FAILED:
                logging.info(
                    "Coordinator of Namespace: %s, job id: %s run failed."
                    % (self.__namespace, self.__id))
                yield self.__do_run_failed()
                break

            yield gen.sleep(const.RETRY_INTERVAL)

    def __gen_resource_request(self):
        client_number = const.DEFAULT_CLIENT_NUM
        if "hyper_parameters" in self.__job_config:
            client_number = \
                self.__job_config["hyper_parameters"].get(
                    "client_num", const.DEFAULT_CLIENT_NUM)

        request_resource = ClientRequirement(
            number=client_number,
            conditions={"runtime": self.__job_config["runtime"]},
            clients=self.__job_config.get("clients"))

        return request_resource

    @gen.coroutine
    def __check_clients_resource(self):
        retry_time = 0
        while retry_time < const.RESOURCE_CHECK_MAX_TIMES:
            if self.__status.state not in [State.PENDING, State.STARTING]:
                self.__starting_process_stopped = True
                return

            try:
                request_resource = self.__gen_resource_request()
                result = yield unary_call(SelectServiceStub,
                                          "CheckClientsResource",
                                          request_resource,
                                          const.SELECTOR_ADDRESS, None)

                if result.state == "success":
                    logging.info("Namespace: %s, job id: %s request clients "
                                 "resource successfully.",
                                 self.__namespace, self.__id)

                    if self.__status.state == State.PENDING:
                        self.__update_status({"state": State.STARTING,
                                              "reason": None,
                                              "progress": 0})

                    return

                logging.error("Namespace: %s, job id: %s request clients "
                              "resource failed, request resource: %s.",
                              self.__namespace, self.__id, request_resource)

                self.__update_status({"state": State.PENDING,
                                      "reason": result.reason,
                                      "progress": 0})

                yield gen.sleep(const.RETRY_INTERVAL)
            except Exception as error:  # pylint:disable=broad-except
                logging.error(str(error))
                logging.error("System error: Fail to request clients resource.")
                yield gen.sleep(const.RETRY_INTERVAL)

        err_msg = "No enough clents resource can satisfy job request."
        raise errors.NoEnoughClientsResource(err_msg)

    @gen.coroutine
    def start(self):
        """start fl job"""
        try:
            self.__stop_heart_timer()
            self.__first_heartbeat_received = False

            if self.__job_config.get("checkpoint_id"):
                self.assert_checkpoint_existing(
                    self.__job_config.get("checkpoint_id"))

            self.__update_status({"state": State.STARTING,
                                  "reason": None,
                                  "progress": 0})

            yield self.__check_clients_resource()
            yield self.__do_create_proxy_route()
            yield self.__do_create_coordinator()

            yield self.__wait_coordinator_running()
        except (errors.CheckpointNotExist, errors.NoEnoughClientsResource) \
                as err:
            logging.error(str(err))
            self.__update_status({"state": State.FAILED,
                                  "reason": str(err)})
            self.__finish_callback(self.__namespace,
                                   self.__id)
        except errors.ModelNotExist as err:
            logging.error("Namespace: %s, job id: %s ,error info: %s",
                          self.__namespace,
                          self.__id,
                          str(err))
            self.__update_status({"state": State.FAILED,
                                  "reason": str(err)})
            self.__finish_callback(self.__namespace,
                                   self.__id)

    def __loss_heartbeat(self):
        self.__stop_heart_timer()

        state = State.FAILED
        reason = "Server internal error: coordinator run in unknown error."

        logging.error("loss heartbeat: namespace: %s, job id: %s"
                      % (self.__namespace, self.__id))
        self.__update_status({"state": state,
                              "reason": reason})

        self.__finish_callback(self.__namespace,
                               self.__id)

    def __start_heart_timer(self):
        timeout_time = time.time() + const.COORDINATOR_HEARTBEAT_TIMEOUT
        self.__heartbeat_timer = IOLoop.instance().add_timeout(
            timeout_time, self.__loss_heartbeat)

    def __stop_heart_timer(self):
        if self.__heartbeat_timer is not None:
            IOLoop.instance().remove_timeout(self.__heartbeat_timer)
            self.__heartbeat_timer = None

    def __refresh_heart_timer(self):
        self.__stop_heart_timer()
        self.__start_heart_timer()

    def __update_status(self, status):
        self.__status.update(status)
        self.__persist()

    def __update_checkpoints(self, checkpoints):
        self.__checkpoints = checkpoints
        self.__persist()

    @gen.coroutine
    def __do_handle_heartbeat(self, status):
        """
        valid_updating_states: key is job current state, value is supported
            updating state from heartbeat of coordinator.
        """
        expected_heartbeat_state = {
            State.RUNNING: [State.RUNNING, State.FINISHED, State.FAILED],
            State.STARTING: [State.RUNNING, State.FINISHED, State.FAILED],
            State.STOPPING: [State.STOPPING, State.STOPPED]}

        if self.__status.state in expected_heartbeat_state.keys():
            if status["state"] \
                    not in expected_heartbeat_state[self.__status.state]:
                logging.warning(
                    "Namespace: %s, job id: %s is in state: %s, not support "
                    "update coordinator heartbeat state: %s", self.__namespace,
                    self.__id, self.__status.state, status["state"])
                return

            self.__refresh_heart_timer()
            self.__update_status(status)
            self.__update_checkpoints(status.get("checkpoints", {}))

            if status["state"] in [State.FAILED, State.FINISHED]:
                self.__stop_heart_timer()
                yield self.__do_delete_coordinator()

                if self.__status.state not in [State.STARTING, State.PENDING]:
                    self.__finish_callback(self.__namespace,
                                           self.__id)
        else:
            logging.warning("Namespace: %s, job id: %s in state: %s, no need "
                            "to handle heartbeat.", self.__namespace, self.__id,
                            self.__status.state)

    @gen.coroutine
    def handle_heartbeat(self, status):
        """
        Handle heartbeat from coordinator

        Args:
            status: heartbeat info about job status
        """

        if self.__first_heartbeat_received:
            yield self.__do_handle_heartbeat(status)
        else:
            logging.info("Namespace: %s, job id: %s receive first heartbeat.",
                         self.__namespace, self.__id)
            self.__first_heartbeat_received = True

    def assert_model_existing(self, job_config):
        """Assert the model exist in the job config.
        """
        if job_config.get("checkpoint_id"):
            self.assert_checkpoint_existing(job_config["checkpoint_id"])
            return

        if job_config.get("model_id"):
            self.assert_model_id_existing(job_config["model_id"])
            return

        if job_config.get("model_path"):
            self.assert_model_path_existing(job_config["model_path"])

    def assert_model_id_existing(self, model_id):
        """Assert the mode if exist in model manager.

        Args:
             model_id: the model unique id.

        Raises:
            ModelNotExist: raise if the model not existing.
        """
        model_client = ModelClient()
        if not model_client.exist(model_id):
            raise errors.ModelNotExist(
                "Not found model with id: %s" % model_id)

    def assert_model_path_existing(self, model_path):
        """Assert the model path exist in the cloud

        Args:
             model_path: the model storage path in the namespace.

        Raises:
            ModelNotExist: raise if the model not existing.
        """
        model_absolute_path = os.path.join(const.WORKSPACE,
                                           self.__namespace,
                                           model_path.lstrip("/"))
        if not os.path.exists(model_absolute_path):
            raise errors.ModelNotExist(
                "Model: %s not existing in namespace: %s, job: %s" % (
                    model_path, self.__namespace, self.__id))

    def assert_checkpoint_existing(self, checkpoint_id):
        """
        Assert checkpoint file whether existing.

        Args:
             checkpoint_id: checkpoint not existing.

        Raises:
            CheckpointNotExist: if checkpoint file not existing.
        """
        if checkpoint_id not in self.__checkpoints:
            raise errors.CheckpointNotExist(
                "checkpoint id: %s not existing in namespace: %s, job: %s" % (
                    checkpoint_id, self.__namespace, self.__id))

        ckpt_relative_path = \
            self.__checkpoints[checkpoint_id]["path"]
        ckpt_absolute_path = os.path.join(const.WORKSPACE,
                                          self.__namespace,
                                          ckpt_relative_path.lstrip("/"))

        if not os.path.exists(ckpt_absolute_path):
            raise errors.CheckpointNotExist(
                "checkpoint id: %s not existing in namespace: %s, job: %s" % (
                    checkpoint_id, self.__namespace, self.__id))

    def __persist(self):
        """
        save job to db(update job info to db)
        """
        self.__db_callback(self)

    @gen.coroutine
    def restore(self):
        """
        Restore fl job
        """
        if self.__status.state == State.RUNNING:
            logging.info("start heartbeat: namespace: %s, job id: %s"
                         % (self.__namespace, self.__id))
            self.__refresh_heart_timer()

        if self.__status.state == State.DELETING:
            self.delete()

        if self.__status.state == State.STOPPING:
            self.stop()

    @gen.coroutine
    def __wait_coordinator_deleted(self):
        times = 0

        while True:
            try:
                status = yield self.__get_coordinator_status()
                logging.info("Namespace: %s, job id: %s coordinator state: %s "
                             "in waiting to deleting process.",
                             self.__namespace, self.__id, status)
            except errors.CoordinatorNotExist:
                logging.info(
                    "Coordinator of Namespace: %s, job id: %s deleted."
                    % (self.__namespace, self.__id))
                break

            times += 1
            if times == const.MAX_RETRY_TIMES:
                logging.warning(
                    "Delete coordinator of namespace: %s, job id: %s "
                    "timeout(%s)."
                    % (self.__namespace, self.__id,
                       const.RETRY_INTERVAL * const.MAX_RETRY_TIMES))

            yield gen.sleep(const.RETRY_INTERVAL)

    def update(self, job_config):
        """
        update job

        Args:
            job_config: job config
        """
        self.assert_model_existing(job_config)

        self.__job_config = job_config
        self.__persist()

    @gen.coroutine
    def __wait_starting_process_stopped(self):
        while not self.__starting_process_stopped:
            logging.info("Namespace: %s, job id: %s, waiting starting process "
                         "stopped.", self.__namespace, self.__id)
            yield gen.sleep(const.RETRY_INTERVAL)

        logging.info("Namespace: %s, job id: %s, starting process stopped.",
                     self.__namespace, self.__id)

    @gen.coroutine
    def __stop_starting_process(self, previous_state):
        if previous_state in [State.STARTING, State.PENDING]:
            self.__starting_process_stopped = False
            yield self.__wait_starting_process_stopped()

    @gen.coroutine
    def stop(self):
        """stop job"""
        previous_state = self.__status.state
        self.__update_status({"state": State.STOPPING})

        yield self.__stop_starting_process(previous_state)

        yield self.__do_stop_coordinator()
        self.__stop_heart_timer()

        yield self.__do_delete_coordinator()
        yield self.__do_delete_proxy_route()

        if self.__status.state in [State.STOPPED, State.STOPPING]:
            self.__update_status({"state": State.STOPPED})
            self.__finish_callback(self.__namespace,
                                   self.__id)

    def __gen_coordinator_address(self):
        return "%s-%s:%s" % (self.__namespace, self.__id,
                             self.__job_config["port"])

    @gen.coroutine
    def __do_stop_coordinator(self):
        try:
            status = yield self.__coordinator.status(self.__id,
                                                     self.__namespace)
            logging.info(
                "Namespace: %s, job id: %s current coordinator state: %s in job"
                " state: %s.", self.__namespace, self.__id, status["state"],
                self.__status.state)

            if (status["state"] == State.RUNNING
                    and self.__first_heartbeat_received):
                yield self.__stop_coordinator()
                yield self.__wait_coordinator_stopped()
            else:
                logging.info(
                    "Namespace: %s, job id: %s or its coordinator not running, "
                    "no need to stop.", self.__namespace, self.__id)
        except errors.CoordinatorNotExist:
            logging.info("Namespace: %s, job id: %s coordinator not existing, "
                         "no need to stop.", self.__namespace, self.__id)

    @gen.coroutine
    def __stop_coordinator(self):
        times = 0
        while times <= const.MAX_RETRY_TIMES:
            try:
                yield unary_call(JobStopServiceStub, "Stop", Metadata(),
                                 self.__gen_coordinator_address(), None)
                logging.info(
                    "Namespace: %s, job id: %s, send stop request "
                    "successfully.", self.__namespace, self.__id)
                return
            except Exception as err:  # pylint:disable=broad-except
                logging.exception(str(err))
                times += 1
                yield gen.sleep(const.RETRY_INTERVAL)

        err_msg = "Namespace: %s, job id: %s, send stop request to %s failed." \
                  % (self.__namespace, self.__id,
                     self.__gen_coordinator_address())

        logging.error(err_msg)

    @gen.coroutine
    def __wait_coordinator_stopped(self):
        times = 0
        while times <= const.MAX_RETRY_TIMES * 10:
            if self.__status.state == State.STOPPED:
                logging.info("Namespace: %s, job id: %s, stop coordinator "
                             "successfully.", self.__namespace, self.__id)
                return

            try:
                status = yield self.__coordinator.status(self.__id,
                                                         self.__namespace)
                logging.info("Namespace: %s, job id: %s coordinator state: %s "
                             "in waiting to stopped process.",
                             self.__namespace, self.__id, status)

                if status["state"] != State.RUNNING:
                    logging.warning(
                        "Namespace: %s, job id: %s coordinator not running, "
                        "no need to wait stopped.", self.__namespace, self.__id)
                    return
            except errors.CoordinatorNotExist:
                logging.info(
                    "Namespace: %s, job id: %s coordinator not existing, "
                    "no need to wait stopped.", self.__namespace, self.__id)
                return

            yield gen.sleep(const.RETRY_INTERVAL)

        err_msg = "Namespace: %s, job id: %s, wait coordinator stopped " \
                  "timeout." % (self.__namespace, self.__id)
        logging.error(err_msg)

    @gen.coroutine
    def delete(self):
        """Delete fl job"""
        self.__update_status({"state": State.DELETING})

        self.__stop_heart_timer()
        yield self.__do_delete_coordinator()
        yield self.__do_delete_proxy_route()

        self.__delete_ckpts()
        self.__do_delete_successfully()

    def __delete_ckpts(self):
        for _ in range(MAX_TRY_DELETE_CKPT):
            try:
                self.__do_delete_ckpts()
                return
            except Exception as err:
                logging.exception(str(err))
        logging.warning("Delete checkpoint failed.")

    def __do_delete_ckpts(self):
        ouput_root = os.path.join(const.WORKSPACE,
                                  self.__namespace,
                                  self.__job_config["output"].lstrip("/"))
        if not os.path.exists(ouput_root):
            return

        dirs = os.listdir(ouput_root)
        job_dir_pattern = "fl_%s_output_V*" % self.__id

        for dir_name in dirs:
            if re.search(job_dir_pattern, dir_name):
                shutil.rmtree(os.path.join(
                    const.WORKSPACE, self.__namespace,
                    self.__job_config["output"].lstrip("/"),
                    dir_name))

    def __do_delete_successfully(self):
        self.__delete_callback(self.__namespace,
                               self.__id)

    @property
    def create_time(self):
        """
        return create time of job
        """
        return self.__create_time

    @property
    def id(self):  # pylint:disable=invalid-name
        """
        return id of job
        """
        return self.__id

    @property
    def namespace(self):
        """
        return namespace of job
        """
        return self.__namespace

    @property
    def status(self):
        """
        return status of job
        """
        return self.__status

    @property
    def checkpoints(self):
        """return checkpoints
        """
        return self.__checkpoints

    @property
    def job_config(self):
        """return job config
        """
        return self.__job_config

    def reset_start_time(self):
        """reset start time"""
        self.__start_time = time.strftime("%Y-%m-%d %H:%M:%S",
                                          time.localtime())
        self.__persist()

    def to_dict(self):
        """
        Convert fl job object to dict.

        Returns:
            fl job info in dict type.
        """
        job_info = deepcopy(self.__job_config)

        job_info["namespace"] = self.__namespace
        job_info["create_time"] = self.__create_time
        job_info["status"] = self.__status.to_dict()
        job_info["start_time"] = self.__start_time
        job_info["checkpoints"] = self.__checkpoints

        return job_info

    def __gen_coordinator_cfg(self):
        coordinator_info = deepcopy(self.__job_config)

        coordinator_info["namespace"] = self.__namespace
        coordinator_info["job-id"] = "%s-%s" % (self.__namespace,
                                                self.__id)
        coordinator_info["job_name"] = coordinator_info["id"]

        if "checkpoint_id" in coordinator_info:
            coordinator_info["model_path"] = \
                self.__checkpoints[
                    coordinator_info["checkpoint_id"]].get("path", "")

        elif coordinator_info.get("model_id"):
            coordinator_info["model"] = self.__parse_model_by_id(
                coordinator_info["model_id"])

        return coordinator_info

    def __parse_model_by_id(self, model_id):
        """Try to access model info by its id.
        """
        model_client = ModelClient()
        model_info = model_client.get_model(model_id)
        if not model_info:
            raise errors.ModelNotExist(
                "Not found model with id: %s" % model_id)

        storage_info = model_info["storage_info"]
        model_namespace, model_path = storage_info[0], storage_info[1]
        return {"model_namespace": model_namespace,
                "model_path": model_path}
