#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=missing-function-docstring, missing-class-docstring
# pylint:disable=protected-access, unused-argument, too-few-public-methods
# pylint:disable=invalid-name
"""
test functions of Schedulers
"""
import asyncio
import unittest
from queue import Queue
from mock import patch

from tornado import ioloop
from tornado import gen

from neursafe_fl.python.job_scheduler.job import Job, State
from neursafe_fl.python.job_scheduler.scheduler import Scheduler, JobKey
import neursafe_fl.python.job_scheduler.util.errors as errors
from neursafe_fl.python.libs.db.mongo.mongo import MongoDB
from neursafe_fl.python.libs.db.errors import DataNotExisting


class FakeDB:

    def __init__(self, *args, **kwargs):
        pass

    def get_collection(self, *args, **kwargs):
        return FakeCollection()


class FakeCollection:
    def insert(self, *args, **kwargs):
        pass

    def delete(self, *args, **kwargs):
        pass

    def update(self, *args, **kwargs):
        pass

    def replace(self, *args, **kwargs):
        pass

    def find(self, *args, **kwargs):
        pass

    def find_one(self, *args, **kwargs):
        pass

    def find_all(self, *args, **kwargs):
        pass


class TestScheduler(unittest.TestCase):

    @patch.object(MongoDB, "__init__", FakeDB.__init__)
    @patch.object(MongoDB, "get_collection", FakeDB.get_collection)
    def setUp(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        self.__job_config = {"id": "job1",
                             "description": "test",
                             "model_path": "/test"}
        self.__namespace = "test"

        self.__scheduler = Scheduler()

    @patch.object(FakeCollection, "find_all")
    @patch.object(Job, "restore")
    @patch.object(Queue, "put")
    def test_scheduler_restore_jobs_successfully(self,
                                                 mock_put,
                                                 mock_restore,
                                                 mock_find):
        jobs = [{"namespace": "n1",
                 "id": "job1",
                 "status": {"state": State.RUNNING}},
                {"namespace": "n2",
                 "id": "job2",
                 "status": {"state": State.QUEUING}},
                {"namespace": "n2",
                 "id": "job3",
                 "status": {"state": State.DELETING}},
                {"namespace": "n2",
                 "id": "job4",
                 "status": {"state": State.FAILED}}]

        mock_find.return_value = jobs

        self.__scheduler._Scheduler__restore_jobs()

        mock_restore.assert_called()
        self.assertEqual(mock_restore.call_count, 2)
        mock_put.assert_called()
        self.assertEqual(mock_put.call_count, 1)
        mock_find.assert_called()
        self.assertEqual(mock_find.call_count, 1)

    @patch.object(FakeCollection, "find_all")
    @patch.object(Job, "start")
    @patch.object(Scheduler, "_Scheduler__schedule_jobs")
    def test_schedule_queuing_jobs_successfully(self,
                                                mock_schedule_jobs,
                                                mock_start,
                                                mock_find):
        jobs = [{"namespace": "n1",
                 "id": "job1",
                 "create_time": "1",
                 "status": {"state": State.QUEUING}},
                {"namespace": "n2",
                 "id": "job2",
                 "create_time": "2",
                 "status": {"state": State.QUEUING}},
                {"namespace": "n2",
                 "id": "job3",
                 "create_time": "3",
                 "status": {"state": State.QUEUING}}]

        @gen.coroutine
        def _fake_start():
            pass

        @gen.coroutine
        def __schedule_jobs():
            # simulate schedule jobs
            while True:
                if self.__scheduler._Scheduler__jobs_queue.empty():
                    break

                job = self.__scheduler._Scheduler__jobs_queue.get()
                if JobKey(job.namespace, job.id) in self.__scheduler.\
                        _Scheduler__active_jobs:
                    yield self.__scheduler._Scheduler__do_schedule_job(job)

        mock_find.return_value = jobs
        mock_start.side_effect = _fake_start
        mock_schedule_jobs.side_effect = __schedule_jobs
        self.__scheduler._Scheduler__restore_jobs()
        ioloop.IOLoop.current().run_sync(self.__scheduler.
                                         _Scheduler__schedule_jobs)

        mock_start.assert_called()
        self.assertEqual(mock_start.call_count, 3)

    @patch.object(FakeCollection, "insert")
    @patch.object(Queue, "put")
    @patch.object(FakeCollection, "find_one")
    @patch.object(Job, "assert_model_existing")
    def test_create_job_successfully(self,
                                     mock_exist,
                                     mock_find,
                                     mock_put,
                                     mock_insert):
        mock_find.side_effect = DataNotExisting
        mock_exist.return_value = True
        self.__scheduler.create_job(self.__namespace, self.__job_config)

        mock_put.assert_called()
        self.assertEqual(mock_put.call_count, 1)
        mock_insert.assert_called()
        self.assertEqual(mock_insert.call_count, 1)

    @patch.object(FakeCollection, "insert")
    @patch.object(Queue, "put")
    @patch.object(FakeCollection, "find")
    def test_raise_exception_when_create_job_if_job_already_exist(self,
                                                                  mock_find,
                                                                  mock_put,
                                                                  mock_insert):
        mock_find.return_value = None

        self.assertRaises(errors.JobExist, self.__scheduler.create_job,
                          self.__namespace, self.__job_config)

        mock_put.assert_not_called()
        mock_insert.assert_not_called()

    @patch.object(FakeCollection, "delete")
    @patch.object(FakeCollection, "find")
    @patch.object(Job, "delete")
    def test_delete_job_successfully(self,
                                     mock_delete_job,
                                     mock_find,
                                     mock_delete):
        @gen.coroutine
        def _fake_delete_job(*args, **kwargs):
            self.__scheduler._Scheduler__job_delete_callback(
                self.__namespace, self.__job_config["id"])

        job = Job(self.__namespace, self.__job_config,
                  {"db_callback": None,
                   "delete_callback": None,
                   "finish_callback": None})
        job_key = JobKey(job.namespace,
                         job.id)

        mock_delete_job.side_effect = _fake_delete_job
        self.__scheduler._Scheduler__active_jobs = {job_key: job}
        mock_find.return_value = job.to_dict()
        self.__scheduler.delete_job(self.__namespace, self.__job_config["id"])

        mock_delete.assert_called()
        self.assertEqual(mock_delete.call_count, 1)
        mock_delete_job.assert_called()
        self.assertEqual(mock_delete_job.call_count, 1)

    @patch.object(FakeCollection, "find_one")
    def test_get_job_successfully(self,
                                  mock_find):
        job = Job(self.__namespace, self.__job_config,
                  {"db_callback": None,
                   "delete_callback": None,
                   "finish_callback": None})
        mock_find.return_value = job.to_dict()

        job = self.__scheduler.get_job(self.__namespace,
                                       self.__job_config["id"])
        self.assertEqual(job["id"], self.__job_config["id"])
        self.assertEqual(job["namespace"], self.__namespace)

    @patch.object(FakeCollection, "find_one")
    def test_raise_exception_when_get_job_if_job_not_exist(self,
                                                           mock_find):
        mock_find.side_effect = DataNotExisting

        self.assertRaises(errors.JobNotExist,
                          self.__scheduler.get_job,
                          self.__namespace, "job_id")

        try:
            self.__scheduler.get_job(self.__namespace, "job_id")
        except errors.JobNotExist as err:
            self.assertEqual(str(err), "namespace: test, "
                                       "job id: job_id not exist.")

    @patch.object(FakeCollection, "find_one")
    def test_raise_exception_when_get_job_if_namespace_not_exist(self,
                                                                 mock_find):
        mock_find.side_effect = DataNotExisting
        self.assertRaises(errors.JobNotExist,
                          self.__scheduler.get_job,
                          "namespace", "job_id")

        try:
            self.__scheduler.get_job("namespace", "job_id")
        except errors.JobNotExist as err:
            self.assertEqual(str(err), "namespace: namespace, "
                                       "job id: job_id not exist.")

    @patch.object(FakeCollection, "find")
    def test_get_jobs_of_namespace_successfully(self, mock_find):
        job = Job(self.__namespace, self.__job_config,
                  {"db_callback": None,
                   "delete_callback": None,
                   "finish_callback": None})

        job2 = Job(self.__namespace, {"id": "job2",
                                      "description": "test"},
                   {"db_callback": None,
                    "delete_callback": None,
                    "finish_callback": None})

        mock_find.return_value = [job.to_dict(), job2.to_dict()]

        jobs = self.__scheduler.get_jobs(self.__namespace)
        self.assertEqual(jobs, [job.to_dict(), job2.to_dict()])

    @patch.object(FakeCollection, "find")
    def test_return_empty_when_get_jobs_if_namespace_not_exist(self,
                                                               mock_find):
        mock_find.return_value = iter([])

        res = self.__scheduler.get_jobs("namespace")
        self.assertEqual(res, [])

    @patch.object(Job, "update")
    @patch.object(FakeCollection, "find_one")
    def test_update_job_successfully(self, mock_find, mock_update):
        job = Job(self.__namespace, self.__job_config,
                  {"db_callback": None,
                   "delete_callback": None,
                   "finish_callback": None})
        mock_find.return_value = job.to_dict()

        self.__scheduler.update_job(self.__namespace,
                                    self.__job_config["id"],
                                    self.__job_config)

        mock_update.assert_called()
        self.assertEqual(mock_update.call_count, 1)

    @patch.object(FakeCollection, "find_one")
    def test_raise_exception_when_update_if_job_not_exist(self, mock_find):
        mock_find.side_effect = DataNotExisting

        self.assertRaises(errors.JobSchedulerError, self.__scheduler.update_job,
                          self.__namespace, self.__job_config["id"],
                          self.__job_config)

        try:
            self.__scheduler.update_job(self.__namespace,
                                        self.__job_config["id"],
                                        self.__job_config)
        except errors.JobSchedulerError as error:
            self.assertEqual(str(error), "namespace: test, job id: "
                                         "job1 not exist.")

    @patch.object(FakeCollection, "find_one")
    def test_raise_exception_when_update_if_job_id_not_same(self, mock_find):
        job = Job(self.__namespace, self.__job_config,
                  {"db_callback": None,
                   "delete_callback": None,
                   "finish_callback": None})
        mock_find.return_value = job.to_dict()

        self.assertRaises(errors.JobSchedulerError, self.__scheduler.update_job,
                          self.__namespace, "different",
                          self.__job_config)

        try:
            self.__scheduler.update_job(self.__namespace,
                                        "different",
                                        self.__job_config)
        except errors.JobSchedulerError as error:
            self.assertEqual(str(error), "Namespace: test, job id: different, "
                                         "error: job id different from id in "
                                         "job config: {'id': 'job1', "
                                         "'description': 'test', "
                                         "'model_path': '/test'}.")

    @patch.object(Queue, "put")
    @patch.object(FakeCollection, "find_one")
    def test_start_successfully(self, mock_find, mock_put):
        job = Job(self.__namespace, self.__job_config,
                  {"db_callback": None,
                   "delete_callback": None,
                   "finish_callback": None})
        mock_find.return_value = job.to_dict()

        self.__scheduler.start_job(self.__namespace,
                                   self.__job_config["id"])

        mock_put.assert_called()
        self.assertEqual(mock_put.call_count, 1)

    @patch.object(FakeCollection, "find_one")
    def test_raise_exception_when_start_job_if_job_not_exist(self, mock_find):
        mock_find.side_effect = DataNotExisting

        self.assertRaises(errors.JobSchedulerError, self.__scheduler.start_job,
                          self.__namespace, self.__job_config["id"])

        try:
            self.__scheduler.start_job(self.__namespace,
                                       self.__job_config["id"])
        except errors.JobSchedulerError as error:
            self.assertEqual(str(error), "namespace: test, job id: "
                                         "job1 not exist.")

    @patch.object(Job, "stop")
    @patch.object(FakeCollection, "find_one")
    def test_stop_successfully(self, mock_find, mock_stop):
        job = Job(self.__namespace, self.__job_config,
                  {"db_callback": None,
                   "delete_callback": None,
                   "finish_callback": None})
        mock_find.return_value = job.to_dict()

        self.__scheduler.stop_job(self.__namespace,
                                  self.__job_config["id"])

        mock_stop.assert_called()
        self.assertEqual(mock_stop.call_count, 1)

    @patch.object(FakeCollection, "find_one")
    def test_raise_exception_when_stop_job_if_job_not_exist(self, mock_find):
        mock_find.side_effect = DataNotExisting

        self.assertRaises(errors.JobSchedulerError, self.__scheduler.stop_job,
                          self.__namespace, self.__job_config["id"])

        try:
            self.__scheduler.stop_job(self.__namespace,
                                      self.__job_config["id"])
        except errors.JobSchedulerError as error:
            self.assertEqual(str(error), "namespace: test, job id: "
                                         "job1 not exist.")


if __name__ == '__main__':
    unittest.main()
