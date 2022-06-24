#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=invalid-name
"""
1.schedule federated learning job.
2.manage life cycle of federated learning jobs.
3.trace job status.
"""
import collections
from queue import Queue
from absl import logging

from tornado import gen

from neursafe_fl.python.job_scheduler.job import Job, State, Operation
import neursafe_fl.python.job_scheduler.util.errors as errors
from neursafe_fl.python.job_scheduler.util.const import RETRY_INTERVAL
from neursafe_fl.python.libs.db.db_factory import create_db
import neursafe_fl.python.job_scheduler.util.const as const
from neursafe_fl.python.job_scheduler.util.operation_retry import \
    db_operation_retry
from neursafe_fl.python.libs.db.errors import DataNotExisting
from neursafe_fl.python.job_scheduler.util.abnormal_exit import exit_abnormally


JobKey = collections.namedtuple("JobKey", ["namespace", "id"])


class Scheduler:
    """
    Manage life cycle of fl jobs.
    """

    def __init__(self):
        self.__jobs_queue = Queue()
        # active jobs include jobs which state is running, queuing, starting,
        #   stopping, deleting
        self.__active_jobs = {}

        self.__db_collection = create_db(const.DB_TYPE,
                                         db_server=const.DB_ADDRESS,
                                         db_name=const.DB_NAME,
                                         user=const.DB_USERNAME,
                                         pass_word=const.DB_PASSWORD).\
            get_collection(const.DB_COLLECTION_NAME)
        self.__clients_selector = None

    def __restore_jobs(self):
        job_configs = self.__db_collection.find_all(
            sorts=[{"key": "start_time"}])

        for job_config in job_configs:
            namespace = job_config["namespace"]

            job = Job(namespace, job_config,
                      {"db_callback": self.__update_to_db,
                       "delete_callback": self.__job_delete_callback,
                       "finish_callback": self.__job_finished_callback})

            if job.status.state in [State.QUEUING, State.STARTING,
                                    State.PENDING]:
                self.__jobs_queue.put(job)

            if job.status.state in [State.RUNNING, State.DELETING,
                                    State.STOPPING]:
                job.restore()

            if job.status.state in [State.QUEUING, State.RUNNING,
                                    State.STARTING, State.PENDING]:
                self.__active_jobs[JobKey(job.namespace, job.id)] = job

    @gen.coroutine
    def __do_schedule_job(self, job):
        yield job.start()

    @gen.coroutine
    def __schedule_jobs(self):
        while True:
            try:
                if not self.__jobs_queue.empty():
                    job = self.__jobs_queue.get()
                    if JobKey(job.namespace, job.id) not in self.__active_jobs:
                        waring_msg = "namespace: %s, job id: %s already " \
                                     "deleted in active jobs." \
                                     % (job.namespace, job.id)
                        logging.warning(waring_msg)
                        continue

                    yield self.__do_schedule_job(job)
                else:
                    logging.debug("jobs queue is empty, wait new "
                                  "job added in job queue.")
                    yield gen.sleep(RETRY_INTERVAL)
            except Exception as error:  # pylint:disable=broad-except
                logging.exception(str(error))
                err_msg = "schedule jobs error, job scheduler exit."
                exit_abnormally(err_msg)

    @gen.coroutine
    def start(self):
        """
        Start job scheduler
        """
        self.__restore_jobs()
        self.__schedule_jobs()

    def __job_delete_callback(self, namespace, job_id):
        self.__job_finished_callback(namespace, job_id)
        self.__delete_in_db(namespace, job_id)

    def __job_finished_callback(self, namespace, job_id):
        if JobKey(namespace, job_id) in self.__active_jobs:
            del self.__active_jobs[JobKey(namespace, job_id)]

    def __assert_job_exist(self, namespace, job_id):
        try:
            indexes = {"namespace": namespace,
                       "id": job_id}
            self.__get_from_db(indexes)
        except DataNotExisting:
            err_msg = "namespace: %s, job id: %s not exist." % (namespace,
                                                                job_id)
            raise errors.JobNotExist(err_msg) from DataNotExisting

    def __assert_job_not_exist(self, namespace, job_id):
        try:
            self.__assert_job_exist(namespace, job_id)

            err_msg = "namespace: %s, job id: %s already exist" \
                      % (namespace, job_id)
            raise errors.JobExist(err_msg)
        except errors.JobNotExist:
            pass

    def __assert_ckpt_id_param_not_exists(self, namespace, job_id, ckpt_id):
        if ckpt_id:
            raise errors.CheckpointNotExist(
                "No checkponits existing in creating namespace: %s job: %s, "
                "Please delete checkpoint id in job config." % (namespace,
                                                                job_id))

    def create_job(self, namespace, job_config):
        """
        Create fl job

        Args:
            namespace: job belongs to which namespace
            job_config: fl job config.
        """
        job_id = job_config["id"]
        self.__assert_job_not_exist(namespace, job_id)
        self.__assert_ckpt_id_param_not_exists(namespace, job_id,
                                               job_config.get("checkpoint_id"))

        job = Job(namespace, job_config,
                  {"db_callback": self.__update_to_db,
                   "delete_callback": self.__job_delete_callback,
                   "finish_callback": self.__job_finished_callback})
        job.assert_model_existing(job_config)

        self.__insert_to_db(job)
        self.__active_jobs[JobKey(job.namespace, job.id)] = job
        self.__jobs_queue.put(job)

    def __gen_job_from_db(self, namespace, job_id):
        job_config = self.__get_from_db({"namespace": namespace,
                                         "id": job_id})
        job = Job(namespace, job_config,
                  {"db_callback": self.__update_to_db,
                   "delete_callback": self.__job_delete_callback,
                   "finish_callback": self.__job_finished_callback})

        return job

    def update_job(self, namespace, job_id, job_config):
        """
        Update fl job

        Args:
            namespace: job belongs to which namespace.
            job_id: job index.
            job_config: fl job config.
        """
        # TODO: optimize performance according to db writing speed.
        self.__assert_job_exist(namespace, job_id)

        if job_id != job_config["id"]:
            raise errors.JobSchedulerError(
                "Namespace: %s, job id: %s, error: job id different from id in "
                "job config: %s." % (namespace, job_id, job_config))

        job_key = JobKey(namespace, job_id)
        if job_key in self.__active_jobs:
            self.__active_jobs[job_key].assert_operation_valid(Operation.UPDATE)
            self.__active_jobs[job_key].update(job_config)
        else:
            job = self.__gen_job_from_db(namespace, job_id)
            job.assert_operation_valid(Operation.UPDATE)
            job.update(job_config)

    def start_job(self, namespace, job_id):
        """
        Start fl job

        Args:
            namespace: job belongs to which namespace
            job_id: job index.
        """
        self.__assert_job_exist(namespace, job_id)

        job_key = JobKey(namespace, job_id)
        if job_key in self.__active_jobs:
            self.__active_jobs[job_key].assert_operation_valid(Operation.START)
            self.__active_jobs[job_key].start()
        else:
            job = self.__gen_job_from_db(namespace, job_id)

            if job.job_config.get("checkpoint_id"):
                job.assert_checkpoint_existing(
                    job.job_config.get("checkpoint_id"))

            job.reset_start_time()
            self.__active_jobs[JobKey(job.namespace, job.id)] = job
            self.__jobs_queue.put(job)

    def stop_job(self, namespace, job_id):
        """
        stop fl job

        Args:
            namespace: job belongs to which namespace
            job_id: job index.
        """
        self.__assert_job_exist(namespace, job_id)

        job_key = JobKey(namespace, job_id)
        if job_key in self.__active_jobs:
            self.__active_jobs[job_key].assert_operation_valid(Operation.STOP)
            self.__active_jobs[job_key].stop()
        else:
            job = self.__gen_job_from_db(namespace, job_id)
            job.assert_operation_valid(Operation.STOP)
            job.stop()

    def delete_job(self, namespace, job_id):
        """
        Delete fl job

        Args:
            namespace: specified namespace
            job_id: job index
        """
        try:
            self.__assert_job_exist(namespace, job_id)

            job_key = JobKey(namespace, job_id)

            if job_key in self.__active_jobs:
                self.__active_jobs[job_key].assert_operation_valid(
                    Operation.DELETE)
                self.__active_jobs[job_key].delete()
            else:
                job = self.__gen_job_from_db(namespace, job_id)

                job.assert_operation_valid(Operation.DELETE)
                job.delete()
        except errors.JobNotExist:
            warning_msg = "namespace: %s, job id: %s already deleted." \
                          % (namespace, job_id)
            logging.warning(warning_msg)

    def get_jobs(self, namespace):
        """
        Get all jobs of namespace

        Args:
            namespace: specified namespace

        Returns:
            jobs list of namespace
        """
        jobs = []
        try:
            for job in self.__get_from_db({"namespace": namespace},
                                          single=False):
                jobs.append(job)
        except DataNotExisting as error:
            logging.warning(str(error))

        return jobs

    def get_job(self, namespace, job_id):
        """
        Get job

        Args:
            namespace: specified namespace
            job_id: job index

        Returns:
            job info
        """
        self.__assert_job_exist(namespace, job_id)

        return self.__get_from_db({"namespace": namespace,
                                   "id": job_id})

    @gen.coroutine
    def handle_heartbeat(self, job_status):
        """
        Handle heartbeat from coordinator of job, heartbeat contain job status
        info

       Args:
           namespace: specified namespace
           job_id: job index
           job_status: job status info
        """
        namespace = job_status["namespace"]
        job_id = job_status["id"]
        if JobKey(namespace, job_id) in self.__active_jobs:
            job = self.__active_jobs[JobKey(namespace, job_id)]
            yield job.handle_heartbeat(job_status)
        else:
            warning_msg = "namespace: %s, job id: %s not in active jobs, " \
                          "heartbeat invalid." % (namespace, job_id)
            logging.warning(warning_msg)

    @db_operation_retry
    def __get_from_db(self, indexes, single=True):
        if single:
            return self.__db_collection.find_one(indexes)

        return self.__db_collection.find(indexes)

    @db_operation_retry
    def __insert_to_db(self, job):
        self.__db_collection.insert(job.to_dict())

    @db_operation_retry
    def __delete_in_db(self, namespace, job_id):
        indexes = {"namespace": namespace,
                   "id": job_id}
        self.__db_collection.delete(indexes)

    @db_operation_retry
    def __update_to_db(self, job):
        indexes = {"namespace": job.namespace,
                   "id": job.id}
        self.__db_collection.replace(indexes, job.to_dict())
