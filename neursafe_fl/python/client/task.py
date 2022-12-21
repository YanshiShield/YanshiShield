#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-many-instance-attributes, too-many-arguments, broad-except
# pylint:disable=no-member
"""Task in client. used to process training and evaluation.
"""
import abc
import enum
import time
import asyncio

from absl import logging

from neursafe_fl.python.client.workspace.custom import write_prepared_parameters
from neursafe_fl.python.client.workspace.metrics import read_metrics
from neursafe_fl.python.runtime.runtime_factory import RuntimeFactory
from neursafe_fl.python.utils.file_io import unzip
from neursafe_fl.proto.message_pb2 import TaskResult, Status
from neursafe_fl.proto.reply_service_grpc import TrainReplyServiceStub, \
    EvaluateReplyServiceStub
from neursafe_fl.python.client.executor.errors import FLError
from neursafe_fl.python.client.executor.executor import DEFAULT_TASK_TIMEOUT
from neursafe_fl.python.client.task_config_parser import TaskConfigParser
from neursafe_fl.python.libs.secure.secure_aggregate.ssa import \
    create_ssa_client
from neursafe_fl.python.trans.grpc_call import stream_call
from neursafe_fl.python.client.validation import ParameterError
from neursafe_fl.python.client.worker import Worker, WorkerStatus
import neursafe_fl.python.client.const as const


WAIT_INTERVAL = 1


class TaskType(enum.Enum):
    """Task type.
    """
    train = 1
    evaluate = 2


def create_task(**kwargs):
    """Create training or evaluation task.
    """
    return _TASK_MAP[kwargs['task_type']](**kwargs)


def _decompress_files_in_workspace(task_workspace, files):
    for _, file_in_memory in files:
        unzip(file_in_memory, task_workspace)


def _write_custom_parameters_in_workspace(task_workspace, parameters):
    if parameters:
        write_prepared_parameters(task_workspace, dict(**parameters))


def _now():
    """Acquire current time.
    """
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))


class Task:
    """Task base class.

    Args:
        task_id: The unique task id.
        task_type: Training or Evaluation task.
        workspace: The working path of the client, which saves some
            temporary files, including init weights, custom parameters
            and files, and so on.
        client_config: Client startup config.
        task_info: The task info from server.
        files_from_server: files sent from the server.
        resource: This describes the allocated resources of each executor
            and used to set the resource limit of the executor when it runs.
        kwargs:
            grpc_metadata: The metadata in the grpc header, sent from the
                coordinator, contains model-id, client_id.
            task_dao: An implementation for saving task information.
            handle_finish: When task finished, call this function.
    """
    def __init__(self, task_id, task_type, workspace, client_config,
                 task_info, files_from_server, resource,
                 **kwargs):
        self.task_id = task_id
        self.task_type = task_type
        self.workspace = workspace
        self.grpc_metadata = kwargs.get("grpc_metadata")

        self._client_config = client_config
        self._task_info = task_info
        self._files_from_server = files_from_server
        self._task_config = None
        self.__resource = resource

        self.__task_dao = kwargs['task_dao']
        self.__done_callback = kwargs['handle_finish']
        self._workers = {}

        self._start_time = _now()
        self._stop_time = None
        self._message = None
        self._status = Status.running
        self._executing_task = None

        self._ssa_client = None

    @abc.abstractmethod
    async def _report_failed_to_server(self):
        """Report the task failed to server. This should implement in subclass.
        """

    async def _save_files_to_workspace(self):
        _decompress_files_in_workspace(self.workspace,
                                       self._files_from_server)
        # must put TaskConfigParser after decompress_files,
        # because script and config maybe send by server,
        # they should save in workspace first.
        self._task_config = await TaskConfigParser(
            self._task_info.spec, self.workspace,
            self._client_config['task_config_entry']).parse(self.task_type)

        self.__create_ssa_client_if_need(self._task_info, self._task_config,
                                         self.task_type)

        _write_custom_parameters_in_workspace(
            self.workspace, self._task_info.spec.custom_params)

    def __create_ssa_client_if_need(self, task_info, task_config, task_type):
        algorithm_parameters = task_info.spec.secure_algorithm
        if (algorithm_parameters
                and task_type == TaskType.train.name
                and algorithm_parameters['type'].lower() == 'ssa'):
            handle = "%s-%s" % (task_info.metadata.job_name,
                                task_info.metadata.round)
            task_timeout = task_config[task_type].get('timeout',
                                                      DEFAULT_TASK_TIMEOUT)
            self._ssa_client = create_ssa_client(
                algorithm_parameters['mode'],
                handle=handle,
                server_addr=self._client_config['server'],
                ssl_key=self._client_config.get('ssl', None),
                client_id=self.grpc_metadata["client_id"],
                min_client_num=int(algorithm_parameters['threshold']),
                client_num=int(algorithm_parameters['clients_num']),
                workspace=self.workspace,
                grpc_metadata=self.grpc_metadata,
                ready_timer_interval=task_timeout,
                server_aggregate_interval=int(
                    algorithm_parameters['aggregate_timeout']))
            self._ssa_client.initialize()

    def __gen_worker_id(self, worker_index):
        return self.task_id + '-' + str(worker_index)

    def __gen_distributed_envs(self):
        runtime = self._task_info.spec.runtime
        worker_addresses = {}

        for index in range(len(self.__resource)):
            worker_id = self.__gen_worker_id(index)
            worker_addresses[worker_id] = {"ip": worker_id,
                                           "port": const.WORKER_PORT,
                                           "index": index}

        return RuntimeFactory.gen_distributed_env_vars(
            runtime, worker_addresses=worker_addresses)

    async def __create_workers(self):
        self._workers.clear()

        distributed_envs = self.__gen_distributed_envs()
        for index, resource in enumerate(self.__resource):
            id_ = self.__gen_worker_id(index)
            worker = Worker(id_, self.task_type,
                            client_config=self._client_config,
                            worker_info=self._task_info,
                            worker_config=self._task_config,
                            workspace=self.workspace,
                            distributed_env=distributed_envs[id_],
                            resource_spec=resource,
                            grpc_metadata=self.grpc_metadata)
            await worker.execute()
            self._workers[id_] = worker

    async def __wait_workers_running(self):
        times = 0
        while times < const.WAIT_WORKER_FINISHED_TIMEOUT:
            running_worker_num = 0
            for id_, worker in self._workers.items():
                status = await worker.status()
                logging.debug("Task:%s, Worker: %s status: %s",
                              self.task_id,
                              id_, status)

                if status == WorkerStatus.FAILED:
                    raise FLError("Task:%s, Worker: %s run failed." %
                                  (self.task_id, id_))

                if status == WorkerStatus.RUNNING:
                    logging.debug("Task:%s, Worker: %s begin run.",
                                  self.task_id,
                                  id_)
                    running_worker_num += 1

            if running_worker_num == len(self._workers):
                logging.info("Task:%s, All workers: %s in running.",
                             self.task_id,
                             self._workers.keys())
                return

            times += 1
            await asyncio.sleep(WAIT_INTERVAL)

        logging.error("Task:%s, Wait all workers: %s in running timeout.",
                      self.task_id,
                      self._workers.keys())

        raise FLError("Task:%s, Workers error, can not run successfully." %
                      self.task_id)

    async def __wait_workers_finished(self):
        while True:
            completed_worker_num = 0
            for id_, worker in self._workers.items():
                status = await worker.status()
                logging.debug("Task:%s, Worker: %s status: %s",
                              self.task_id,
                              id_, status)

                if status == WorkerStatus.FAILED:
                    raise FLError("Task: %s, Worker: %s run failed." %
                                  (self.task_id, id_))

                if status == WorkerStatus.COMPLETED:
                    logging.debug("Task: %s, Worker: %s completed.",
                                  self.task_id, id_)
                    completed_worker_num += 1

            if completed_worker_num == len(self._workers):
                logging.info("Task: %s, All worker: %s run completed.",
                             self.task_id, self._workers.keys())
                break

            await asyncio.sleep(WAIT_INTERVAL)

    async def _do_execute(self):
        try:
            await self.__create_workers()
            await self.__wait_workers_running()
            await self.__wait_workers_finished()
        except FLError as err:
            self.__record_error(str(err))
            if self._ssa_client:
                self._ssa_client.finish(success=False)

            await self._report_failed_to_server()
            return

        self.__record_success()
        if self._ssa_client:
            self._ssa_client.finish(success=True)

        logging.info('Task_id:%s run success', self.task_id)

    def __record_success(self):
        self._stop_time = _now()
        self._status = Status.success
        self.__task_dao.update(self._to_dict())

    def __record_error(self, err):
        logging.exception(err)

        self._stop_time = _now()
        self._message = err
        self._status = Status.failed
        self.__task_dao.update(self._to_dict())

    async def execute(self):
        """Run the task.
        """
        try:
            await self._save_files_to_workspace()
        except (FLError, ParameterError) as err:
            self.__record_error(str(err))
            await self._report_failed_to_server()
            return

        self._executing_task = asyncio.create_task(self._do_execute())
        try:
            await self._executing_task
        except asyncio.CancelledError:
            logging.info("Cancel executing task: %s, cancel stated: %s",
                         self.task_id,
                         self._executing_task.cancelled())
        except Exception as err:
            logging.exception(str(err))
        finally:
            self._executing_task = None
            await self._delete_workers()
            self.__done_callback(self)

    async def __wait_workers_deleted(self):
        while True:
            deleted_worker_num = 0
            for id_, worker in self._workers.items():
                status = await worker.status()
                logging.debug("Task:%s, Worker: %s status: %s",
                              self.task_id,
                              id_, status)

                if status == WorkerStatus.DELETED:
                    logging.debug("Task: %s, Worker: %s deleted.",
                                  self.task_id, id_)
                    deleted_worker_num += 1

            if deleted_worker_num == len(self._workers):
                logging.info("Task: %s, All worker: %s deleted.",
                             self.task_id, self._workers.keys())
                break

            await asyncio.sleep(WAIT_INTERVAL)

    async def _delete_workers(self):
        for worker in self._workers.values():
            await worker.delete()

        await self.__wait_workers_deleted()

    def cancel(self):
        """Cancel task.
        """
        if self._executing_task:
            self._executing_task.cancel()

    def _to_dict(self):
        return {
            'id': self.task_id,
            'job_name': self._task_info.metadata.job_name,
            'round': self._task_info.metadata.round,
            'config_file': self._task_info.spec.entry_name,
            'workspace': self.workspace,
            'start_time': self._start_time,
            'stop_time': self._stop_time,
            'status': self._status
        }

    def persist(self):
        """Insert task config to db.
        """
        self.__task_dao.save(self._to_dict())

    def _encode_task_result(self, status, metrics=None, custom_params=None):
        task_result = TaskResult(metadata=self._task_info.metadata,
                                 client_id=self.grpc_metadata["client_id"],
                                 status=status)

        if metrics:
            task_result.spec.metrics.update(metrics)

        if custom_params:
            task_result.spec.custom_params.update(custom_params)

        return task_result

    def _get_metrics(self):
        return read_metrics(self.workspace)

    @property
    def job_name(self):
        """Job name.
        """
        return self._task_info.metadata.job_name

    @property
    def round_num(self):
        """Round num.
        """
        return self._task_info.metadata.round


class TrainTask(Task):
    """Train task.
    """
    async def _report_failed_to_server(self):
        task_result = self._encode_task_result(Status.failed)
        await stream_call(
            TrainReplyServiceStub, 'TrainReply', TaskResult,
            self._client_config['server'], config=task_result,
            certificate_path=self._client_config.get('ssl', None),
            metadata=self.grpc_metadata)


class EvaluateTask(Task):
    """Evaluate task.
    """
    async def _report_failed_to_server(self):
        task_result = self._encode_task_result(Status.failed)
        await stream_call(
            EvaluateReplyServiceStub, 'EvaluateReply', TaskResult,
            self._client_config['server'], config=task_result,
            certificate_path=self._client_config.get('ssl', None),
            metadata=self.grpc_metadata)


_TASK_MAP = {
    TaskType.train.name: TrainTask,
    TaskType.evaluate.name: EvaluateTask
}
