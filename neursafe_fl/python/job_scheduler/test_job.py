#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=missing-function-docstring, missing-class-docstring,
# pylint:disable=unused-argument, protected-access, too-many-arguments
# pylint:disable=too-many-public-methods, too-many-lines, too-many-locals
"""
test function of Job, JobStatus
"""
import time
import asyncio
import unittest
from mock import patch

from tornado import gen
from tornado import ioloop

from neursafe_fl.python.job_scheduler.coordinator import Coordinator
from neursafe_fl.python.job_scheduler.job import JobStatus, State, Job, Operation
from neursafe_fl.python.trans.proxy import Proxy
import neursafe_fl.python.job_scheduler.util.errors as errors


class TestJobStatus(unittest.TestCase):

    def test_init_job_status_successfully(self):
        job_status = JobStatus()
        status = job_status.to_dict()

        self.assertEqual(status, {"state": State.QUEUING,
                                  "reason": None,
                                  "progress": 0})

    def test_update_job_status_successfully(self):
        # update to runing
        job_status = JobStatus()
        job_status.update({"state": State.RUNNING})
        status = job_status.to_dict()

        self.assertEqual(status, {"state": State.RUNNING,
                                  "reason": None,
                                  "progress": 0})

        # update to finished
        job_status.update({"state": State.FINISHED,
                           "progress": 100})
        status = job_status.to_dict()

        self.assertEqual(status, {"state": State.FINISHED,
                                  "reason": None,
                                  "progress": 100})

        # update to failed
        job_status.update({"state": State.FAILED,
                           "reason": "error",
                           "progress": 50})
        status = job_status.to_dict()

        self.assertEqual(status, {"state": State.FAILED,
                                  "reason": "error",
                                  "progress": 50})


def fake_db_callback(*args, **kwargs):
    pass


def fake_delete_callback(*args, **kwargs):
    pass


def fake_finish_callback(*args, **kwargs):
    pass


class FakeInstance:

    def create(self, *args, **kwargs):
        pass

    def delete(self, *args, **kwargs):
        pass

    def status(self, *args, **kwargs):
        pass


class TestJob(unittest.TestCase):

    def setUp(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.__job_config = {"id": "job1",
                             "description": "test",
                             "port": 8080,
                             "output": ""}
        self.__namespace = "test"

    def test_init_job_successfully(self):
        callbacks = {"db_callback": fake_db_callback,
                     "delete_callback": fake_delete_callback,
                     "finish_callback": fake_finish_callback}
        job = Job(self.__namespace,
                  self.__job_config,
                  callbacks)

        self.assertTrue("create_time" in job.to_dict())
        self.assertEqual(job.to_dict()["status"], {"progress": 0,
                                                   "reason": None,
                                                   "state": State.QUEUING})

    def test_return_job_property_successfully(self):
        callbacks = {"db_callback": fake_db_callback,
                     "delete_callback": fake_delete_callback,
                     "finish_callback": fake_finish_callback}
        job = Job(self.__namespace,
                  self.__job_config,
                  callbacks)
        self.assertEqual(type(job.status), JobStatus)
        self.assertEqual(job.id, self.__job_config["id"])
        self.assertEqual(job.namespace, self.__namespace)
        self.assertEqual(type(job.create_time), str)

    @patch.object(Proxy, "add")
    @patch.object(Coordinator, "create")
    @patch.object(Coordinator, "status")
    @patch("neursafe_fl.python.job_scheduler.test_job.fake_db_callback")
    @patch("neursafe_fl.python.job_scheduler.test_job.fake_finish_callback")
    @patch.object(Job, "_Job__check_clients_resource")
    def test_start_job_successfully(self,
                                    mock_check,
                                    mock_finish_callback,
                                    mock_db_callback,
                                    fake_status,
                                    fake_create,
                                    fake_add_route):
        callbacks = {"db_callback": fake_db_callback,
                     "delete_callback": fake_delete_callback,
                     "finish_callback": fake_finish_callback}
        job = Job(self.__namespace,
                  self.__job_config,
                  callbacks)

        @gen.coroutine
        def _add(*args, **kwargs):
            pass

        @gen.coroutine
        def _create(*args, **kwargs):
            pass

        @gen.coroutine
        def _status(*args, **kwargs):
            raise gen.Return({"state": State.RUNNING})

        @gen.coroutine
        def __check():
            pass

        mock_check.side_effect = __check
        fake_status.side_effect = _status
        fake_create.side_effect = _create
        fake_add_route.side_effect = _add

        def receive_heartbeat():
            heartbeat = {"id": self.__job_config["id"],
                         "namespace": self.__namespace,
                         "state": State.RUNNING,
                         "progress": 1}
            job.handle_heartbeat(heartbeat)

        ioloop.IOLoop.instance().add_timeout(
            1, receive_heartbeat)
        ioloop.IOLoop.current().run_sync(job.start)

        fake_create.assert_called()
        self.assertEqual(fake_create.call_count, 1)
        mock_db_callback.assert_called()
        self.assertEqual(mock_db_callback.call_count, 2)
        mock_finish_callback.assert_not_called()
        self.assertEqual(job.status.state, State.RUNNING)

    @patch.object(Proxy, "add")
    @patch.object(Coordinator, "create")
    @patch("neursafe_fl.python.job_scheduler.test_job.fake_db_callback")
    @patch.object(Job, "_Job__wait_coordinator_running")
    @patch.object(Job, "_Job__check_clients_resource")
    def test_start_job_failed_if_create_coordinator_failed(self,
                                                           mock_check,
                                                           mock_wait,
                                                           mock_db_callback,
                                                           fake_create,
                                                           fake_add_route):
        """
        create coordinator failed, it will retry many times, so in test case, it
        will not raise CoordinatorFailed error, we only test create whether
        executing, and mock wait_coordinator_running
        """
        callbacks = {"db_callback": fake_db_callback,
                     "delete_callback": fake_delete_callback,
                     "finish_callback": fake_finish_callback}
        job = Job(self.__namespace,
                  self.__job_config,
                  callbacks)

        @gen.coroutine
        def _create(*args, **kwargs):
            pass

        @gen.coroutine
        def _add(*args, **kwargs):
            pass

        @gen.coroutine
        def __wait(*args, **kwargs):
            pass

        @gen.coroutine
        def __check():
            pass

        mock_check.side_effect = __check
        mock_wait.side_effect = __wait
        fake_add_route.side_effect = _add
        fake_create.side_effect = _create

        ioloop.IOLoop.current().run_sync(job.start)

        fake_create.assert_called()
        self.assertEqual(fake_create.call_count, 1)
        mock_db_callback.assert_called()
        self.assertEqual(mock_db_callback.call_count, 1)
        self.assertEqual(job.status.state, State.STARTING)

    def test_update_job_successfully(self):
        callbacks = {"db_callback": fake_db_callback,
                     "delete_callback": fake_delete_callback,
                     "finish_callback": fake_finish_callback}
        job = Job(self.__namespace,
                  self.__job_config,
                  callbacks)

        new_config = self.__job_config.copy()
        new_config["description"] = "new"
        new_config["port"] = 9090

        job.update(new_config)

        self.assertEqual(job.to_dict()["port"], 9090)
        self.assertEqual(job.to_dict()["description"], "new")

    @patch.object(Proxy, "delete")
    @patch.object(Coordinator, "delete")
    @patch.object(Coordinator, "status")
    @patch("neursafe_fl.python.job_scheduler.test_job.fake_db_callback")
    @patch("neursafe_fl.python.job_scheduler.test_job.fake_delete_callback")
    def test_delete_job_successfully(self,
                                     mock_delete_callback,
                                     mock_db_callback,
                                     fake_status,
                                     fake_delete,
                                     fake_delete_route):
        callbacks = {"db_callback": fake_db_callback,
                     "delete_callback": fake_delete_callback,
                     "finish_callback": fake_finish_callback}
        job = Job(self.__namespace,
                  self.__job_config,
                  callbacks)

        @gen.coroutine
        def _delete(*args, **kwargs):
            pass

        @gen.coroutine
        def _delete_route(*args, **kwargs):
            pass

        @gen.coroutine
        def _status(*args, **kwargs):
            raise errors.CoordinatorNotExist()

        fake_status.side_effect = _status
        fake_delete.side_effect = _delete
        fake_delete_route.side_effect = _delete_route

        ioloop.IOLoop.current().run_sync(job.delete)
        fake_delete.assert_called()
        self.assertEqual(fake_delete.call_count, 1)
        mock_db_callback.assert_called()
        self.assertEqual(mock_db_callback.call_count, 1)
        mock_delete_callback.assert_called()
        self.assertEqual(mock_delete_callback.call_count, 1)

    @patch.object(Proxy, "add")
    @patch.object(Coordinator, "create")
    @patch.object(Job, "_Job__do_delete_coordinator")
    @patch.object(Coordinator, "status")
    @patch("neursafe_fl.python.job_scheduler.test_job.fake_db_callback")
    @patch("neursafe_fl.python.job_scheduler.test_job.fake_finish_callback")
    @patch.object(Job, "_Job__check_clients_resource")
    def test_handle_heartbeat_successfully_if_status_is_finished(
            self, mock_check, mock_finish_callback, mock_db_callback,
            fake_status, fake_delete, fake_create, fake_add_route):
        callbacks = {"db_callback": fake_db_callback,
                     "delete_callback": fake_delete_callback,
                     "finish_callback": fake_finish_callback}
        job = Job(self.__namespace,
                  self.__job_config,
                  callbacks)

        @gen.coroutine
        def _add(*args, **kwargs):
            pass

        @gen.coroutine
        def _create(*args, **kwargs):
            pass

        @gen.coroutine
        def _delete(*args, **kwargs):
            pass

        @gen.coroutine
        def _status(*args, **kwargs):
            raise gen.Return({"state": State.RUNNING})

        @gen.coroutine
        def __check():
            pass

        mock_check.side_effect = __check
        fake_status.side_effect = _status
        fake_create.side_effect = _create
        fake_delete.side_effect = _delete
        fake_add_route.side_effect = _create

        @gen.coroutine
        def receive_heartbeat():
            heartbeat = {"id": self.__job_config["id"],
                         "namespace": self.__namespace,
                         "state": State.RUNNING,
                         "progress": 1}
            yield job.handle_heartbeat(heartbeat)

        ioloop.IOLoop.instance().add_timeout(
            1, receive_heartbeat)

        ioloop.IOLoop.current().run_sync(job.start)

        @gen.coroutine
        def receive_heartbeat_with_finished_state():
            heartbeat = {"id": self.__job_config["id"],
                         "namespace": self.__namespace,
                         "state": State.FINISHED,
                         "progress": 100}
            yield job.handle_heartbeat(heartbeat)

        ioloop.IOLoop.current().run_sync(receive_heartbeat_with_finished_state)

        mock_db_callback.assert_called()
        self.assertEqual(mock_db_callback.call_count, 4)
        mock_finish_callback.assert_called()
        self.assertEqual(mock_finish_callback.call_count, 1)

        self.assertEqual(job.status.state, State.FINISHED)
        self.assertEqual(job.status.progress, 100)
        self.assertEqual(job.status.reason, None)

    @patch.object(Proxy, "add")
    @patch.object(Coordinator, "create")
    @patch.object(Coordinator, "delete")
    @patch.object(Coordinator, "status")
    @patch("neursafe_fl.python.job_scheduler.test_job.fake_db_callback")
    @patch("neursafe_fl.python.job_scheduler.test_job.fake_finish_callback")
    @patch.object(Job, "_Job__check_clients_resource")
    def test_handle_heartbeat_successfully_if_status_is_running(
            self, mock_check, mock_finish_callback, mock_db_callback,
            fake_status, fake_delete, fake_create, fake_add_route):
        callbacks = {"db_callback": fake_db_callback,
                     "delete_callback": fake_delete_callback,
                     "finish_callback": fake_finish_callback}
        job = Job(self.__namespace,
                  self.__job_config,
                  callbacks)

        @gen.coroutine
        def _add(*args, **kwargs):
            pass

        @gen.coroutine
        def _create(*args, **kwargs):
            pass

        @gen.coroutine
        def _delete(*args, **kwargs):
            pass

        @gen.coroutine
        def _status(*args, **kwargs):
            raise gen.Return({"state": State.RUNNING})

        @gen.coroutine
        def __check():
            pass

        mock_check.side_effect = __check
        fake_status.side_effect = _status
        fake_create.side_effect = _create
        fake_delete.side_effect = _delete
        fake_add_route.side_effect = _add

        def receive_heartbeat():
            heartbeat = {"id": self.__job_config["id"],
                         "namespace": self.__namespace,
                         "state": State.RUNNING,
                         "progress": 1}
            job.handle_heartbeat(heartbeat)

        ioloop.IOLoop.instance().add_timeout(
            1, receive_heartbeat)
        ioloop.IOLoop.current().run_sync(job.start)

        heartbeat = {"id": self.__job_config["id"],
                     "namespace": self.__namespace,
                     "state": State.RUNNING,
                     "progress": 80,
                     "checkpoints": {"ck1": {"accuracy": 0.91,
                                             "path": "/xx/xx/xx"}}
                     }
        job.handle_heartbeat(heartbeat)

        mock_db_callback.assert_called()
        self.assertEqual(mock_db_callback.call_count, 4)
        mock_finish_callback.assert_not_called()

        self.assertEqual(job.status.state, State.RUNNING)
        self.assertEqual(job.status.progress, 80)
        self.assertEqual(job.status.reason, None)
        self.assertEqual(job.checkpoints, {"ck1": {"accuracy": 0.91,
                                                   "path": "/xx/xx/xx"}})

    @patch.object(Proxy, "add")
    @patch.object(Coordinator, "create")
    @patch.object(Job, "_Job__do_delete_coordinator")
    @patch.object(Coordinator, "status")
    @patch("neursafe_fl.python.job_scheduler.test_job.fake_db_callback")
    @patch("neursafe_fl.python.job_scheduler.test_job.fake_finish_callback")
    @patch.object(Job, "_Job__check_clients_resource")
    def test_handle_heartbeat_successfully_if_status_is_failed(
            self, mock_check, mock_finish_callback, mock_db_callback,
            fake_status, fake_delete, fake_create, fake_add_route):
        callbacks = {"db_callback": fake_db_callback,
                     "delete_callback": fake_delete_callback,
                     "finish_callback": fake_finish_callback}
        job = Job(self.__namespace,
                  self.__job_config,
                  callbacks)

        @gen.coroutine
        def _create(*args, **kwargs):
            pass

        @gen.coroutine
        def _delete(*args, **kwargs):
            pass

        @gen.coroutine
        def _add(*args, **kwargs):
            pass

        @gen.coroutine
        def _status(*args, **kwargs):
            raise gen.Return({"state": State.RUNNING})

        @gen.coroutine
        def __check():
            pass

        mock_check.side_effect = __check
        fake_status.side_effect = _status
        fake_create.side_effect = _create
        fake_delete.side_effect = _delete
        fake_add_route.side_effect = _add

        @gen.coroutine
        def receive_heartbeat():
            heartbeat = {"id": self.__job_config["id"],
                         "namespace": self.__namespace,
                         "state": State.RUNNING,
                         "progress": 1}
            yield job.handle_heartbeat(heartbeat)

        ioloop.IOLoop.instance().add_timeout(
            1, receive_heartbeat)
        ioloop.IOLoop.current().run_sync(job.start)

        @gen.coroutine
        def receive_heartbeart_with_failed_state():
            heartbeat = {"id": self.__job_config["id"],
                         "namespace": self.__namespace,
                         "state": State.FAILED,
                         "progress": 50,
                         "reason": "run failed."}
            yield job.handle_heartbeat(heartbeat)

        ioloop.IOLoop.current().run_sync(receive_heartbeart_with_failed_state)

        mock_db_callback.assert_called()
        self.assertEqual(mock_db_callback.call_count, 4)

        mock_finish_callback.assert_called()
        self.assertEqual(mock_finish_callback.call_count, 1)

        self.assertEqual(job.status.state, State.FAILED)
        self.assertEqual(job.status.progress, 50)
        self.assertEqual(job.status.reason, "run failed.")

    @patch.object(Proxy, "add")
    @patch.object(Coordinator, "create")
    @patch.object(Coordinator, "status")
    @patch("neursafe_fl.python.job_scheduler.test_job.fake_db_callback")
    @patch("neursafe_fl.python.job_scheduler.test_job.fake_finish_callback")
    @patch.object(Job, "_Job__check_clients_resource")
    def test_handle_heartbeat_successfully_if_status_is_stopped(
            self, mock_check, mock_finish_callback, mock_db_callback,
            fake_status, fake_create, fake_add_route):
        callbacks = {"db_callback": fake_db_callback,
                     "delete_callback": fake_delete_callback,
                     "finish_callback": fake_finish_callback}
        job = Job(self.__namespace,
                  self.__job_config,
                  callbacks)

        @gen.coroutine
        def _create(*args, **kwargs):
            pass

        @gen.coroutine
        def _add(*args, **kwargs):
            pass

        @gen.coroutine
        def _status(*args, **kwargs):
            raise gen.Return({"state": State.RUNNING})

        @gen.coroutine
        def __check():
            pass

        mock_check.side_effect = __check
        fake_status.side_effect = _status
        fake_create.side_effect = _create
        fake_add_route.side_effect = _add

        def receive_heartbeat():
            heartbeat = {"id": self.__job_config["id"],
                         "namespace": self.__namespace,
                         "state": State.RUNNING,
                         "progress": 1}
            job.handle_heartbeat(heartbeat)

        ioloop.IOLoop.instance().add_timeout(
            1, receive_heartbeat)
        ioloop.IOLoop.current().run_sync(job.start)

        job._Job__status.state = State.STOPPING
        heartbeat = {"id": self.__job_config["id"],
                     "namespace": self.__namespace,
                     "state": State.STOPPED,
                     "progress": 50,
                     "reason": None}
        job.handle_heartbeat(heartbeat)

        mock_db_callback.assert_called()
        self.assertEqual(mock_db_callback.call_count, 4)

        self.assertEqual(job.status.state, State.STOPPED)
        self.assertEqual(job.status.progress, 50)

    @patch.object(Proxy, "add")
    @patch.object(Coordinator, "create")
    @patch.object(Coordinator, "status")
    @patch("neursafe_fl.python.job_scheduler.test_job.fake_db_callback")
    @patch("neursafe_fl.python.job_scheduler.test_job.fake_finish_callback")
    @patch.object(Job, "_Job__check_clients_resource")
    def test_run_correctly_if_lose_job_heartbeat(
            self, mock_check, mock_finish_callback, mock_db_callback,
            fake_status, fake_create, fake_add_route):
        callbacks = {"db_callback": fake_db_callback,
                     "delete_callback": fake_delete_callback,
                     "finish_callback": fake_finish_callback}
        job = Job(self.__namespace,
                  self.__job_config,
                  callbacks)

        @gen.coroutine
        def _add(*args, **kwargs):
            pass

        @gen.coroutine
        def _create(*args, **kwargs):
            pass

        @gen.coroutine
        def _status(*args, **kwargs):
            raise gen.Return({"state": State.RUNNING})

        @gen.coroutine
        def __check():
            pass

        mock_check.side_effect = __check
        fake_status.side_effect = _status
        fake_create.side_effect = _create
        fake_add_route.side_effect = _add

        def receive_heartbeat():
            heartbeat = {"id": self.__job_config["id"],
                         "namespace": self.__namespace,
                         "state": State.RUNNING,
                         "progress": 1}
            job.handle_heartbeat(heartbeat)

        ioloop.IOLoop.instance().add_timeout(
            1, receive_heartbeat)
        ioloop.IOLoop.current().run_sync(job.start)
        self.assertEqual(job.status.state, State.RUNNING)

        job._Job__loss_heartbeat()

        self.assertEqual(job.status.state, State.FAILED)
        self.assertEqual(job.status.progress, 0)
        self.assertEqual(job.status.reason, "Server internal error: "
                                            "coordinator run in unknown error.")

        mock_db_callback.assert_called()
        self.assertEqual(mock_db_callback.call_count, 3)
        mock_finish_callback.assert_called()
        self.assertEqual(mock_finish_callback.call_count, 1)

    @patch.object(Proxy, "add")
    @patch.object(Coordinator, "create")
    @patch.object(Coordinator, "status")
    @patch("neursafe_fl.python.job_scheduler.test_job.fake_db_callback")
    @patch("neursafe_fl.python.job_scheduler.test_job.fake_finish_callback")
    @patch.object(Job, "_Job__check_clients_resource")
    def test_run_correctly_if_coordinator_run_failed(self,
                                                     mock_check,
                                                     mock_finish_callback,
                                                     mock_db_callback,
                                                     fake_status,
                                                     fake_create,
                                                     fake_add_route):
        callbacks = {"db_callback": fake_db_callback,
                     "delete_callback": fake_delete_callback,
                     "finish_callback": fake_finish_callback}
        job = Job(self.__namespace,
                  self.__job_config,
                  callbacks)

        @gen.coroutine
        def _add(*args, **kwargs):
            pass

        @gen.coroutine
        def _create(*args, **kwargs):
            pass

        @gen.coroutine
        def _status(*args, **kwargs):
            raise gen.Return({"state": State.FAILED})

        @gen.coroutine
        def __check():
            pass

        mock_check.side_effect = __check
        fake_status.side_effect = _status
        fake_create.side_effect = _create
        fake_add_route.side_effect = _add

        ioloop.IOLoop.current().run_sync(job.start)

        fake_create.assert_called()
        self.assertEqual(fake_create.call_count, 1)
        mock_db_callback.assert_called()
        self.assertEqual(mock_db_callback.call_count, 2)
        self.assertEqual(job.status.state, State.FAILED)
        self.assertEqual(job.status.reason, "Coordinator run failed.")
        self.assertEqual(job.status.progress, 0)
        mock_finish_callback.assert_called()
        self.assertEqual(mock_finish_callback.call_count, 1)

    def test_return_job_info_successfully(self):
        callbacks = {"db_callback": fake_db_callback,
                     "delete_callback": fake_delete_callback,
                     "finish_callback": fake_finish_callback}
        job = Job(self.__namespace,
                  self.__job_config,
                  callbacks)

        self.assertTrue("create_time" in job.to_dict())
        self.assertEqual(job.to_dict()["status"], {"progress": 0,
                                                   "reason": None,
                                                   "state": State.QUEUING})
        self.assertEqual(job.to_dict()["id"], self.__job_config["id"])
        self.assertEqual(job.to_dict()["namespace"], self.__namespace)
        self.assertEqual(job.to_dict()["description"],
                         self.__job_config["description"])

    @patch.object(Job, "_Job__start_heart_timer")
    def test_restore_job_successfully_if_state_is_running(self,
                                                          mock_start_heartbeat):
        callbacks = {"db_callback": fake_db_callback,
                     "delete_callback": fake_delete_callback,
                     "finish_callback": fake_finish_callback}
        job = Job(self.__namespace,
                  self.__job_config,
                  callbacks)

        job._Job__status.state = State.RUNNING
        ioloop.IOLoop.current().run_sync(job.restore)

        mock_start_heartbeat.assert_called()
        self.assertEqual(mock_start_heartbeat.call_count, 1)

    @patch.object(Job, "delete")
    def test_restore_job_successfully_if_state_is_deleting(self,
                                                           fake_delete):
        callbacks = {"db_callback": fake_db_callback,
                     "delete_callback": fake_delete_callback,
                     "finish_callback": fake_finish_callback}
        job = Job(self.__namespace,
                  self.__job_config,
                  callbacks)

        @gen.coroutine
        def _delete(*args, **kwargs):
            pass

        fake_delete.side_effect = _delete
        job._Job__status.state = State.DELETING

        ioloop.IOLoop.current().run_sync(job.restore)

        fake_delete.assert_called()
        self.assertEqual(fake_delete.call_count, 1)

    @patch.object(Proxy, "delete")
    @patch.object(Coordinator, "status")
    @patch("neursafe_fl.python.job_scheduler.test_job.fake_db_callback")
    @patch("neursafe_fl.python.job_scheduler.test_job.fake_delete_callback")
    @patch("neursafe_fl.python.job_scheduler.test_job.fake_finish_callback")
    @patch.object(Job, "_Job__stop_coordinator")
    @patch.object(Job, "_Job__do_delete_coordinator")
    @patch.object(Job, "_Job__stop_starting_process")
    def test_stop_job_successfully(self,
                                   mock_stop_previous_process,
                                   mock_delete_coordinator,
                                   mock_stop,
                                   mock_finish_callback,
                                   mock_delete_callback,
                                   mock_db_callback,
                                   fake_status,
                                   fake_delete_route):
        callbacks = {"db_callback": fake_db_callback,
                     "delete_callback": fake_delete_callback,
                     "finish_callback": fake_finish_callback}
        job = Job(self.__namespace,
                  self.__job_config,
                  callbacks)
        job._Job__status.state = State.RUNNING

        @gen.coroutine
        def _stop(*args, **kwargs):
            pass

        @gen.coroutine
        def _delete_coordinator(*args, **kwargs):
            pass

        @gen.coroutine
        def _delete_route(*args, **kwargs):
            pass

        @gen.coroutine
        def _status(*args, **kwargs):
            raise gen.Return({"state": State.RUNNING})

        @gen.coroutine
        def _stop_previous_process(*args, **kwargs):
            pass

        fake_status.side_effect = _status
        fake_delete_route.side_effect = _delete_route
        mock_stop.side_effect = _stop
        mock_delete_coordinator.side_effect = _delete_coordinator
        mock_stop_previous_process.side_effect = _stop_previous_process

        def receive_heartbeat():
            heartbeat = {"id": self.__job_config["id"],
                         "namespace": self.__namespace,
                         "state": State.STOPPED,
                         "progress": 1}
            job.handle_heartbeat(heartbeat)

        receive_heartbeat()
        ioloop.IOLoop.instance().add_timeout(
            1, receive_heartbeat)
        ioloop.IOLoop.current().run_sync(job.stop)

        mock_db_callback.assert_called()
        self.assertEqual(mock_db_callback.call_count, 4)
        mock_finish_callback.assert_called()
        self.assertEqual(mock_finish_callback.call_count, 1)
        mock_stop.assert_called()
        self.assertEqual(mock_stop.call_count, 1)
        mock_delete_callback.assert_not_called()
        mock_stop_previous_process.assert_called()

        self.assertEqual(job.status.state, State.STOPPED)

    @patch.object(Proxy, "delete")
    @patch.object(Coordinator, "delete")
    @patch.object(Coordinator, "status")
    @patch("neursafe_fl.python.job_scheduler.test_job.fake_db_callback")
    @patch("neursafe_fl.python.job_scheduler.test_job.fake_delete_callback")
    @patch("neursafe_fl.python.job_scheduler.test_job.fake_finish_callback")
    @patch.object(Job, "_Job__stop_coordinator")
    @patch.object(Job, "_Job__stop_starting_process")
    def test_stop_job_successfully_if_coordinator_not_existing(
            self, mock_stop_previous_process, mock_stop, mock_finish_callback,
            mock_delete_callback, mock_db_callback, fake_status, fake_delete,
            fake_delete_route):
        callbacks = {"db_callback": fake_db_callback,
                     "delete_callback": fake_delete_callback,
                     "finish_callback": fake_finish_callback}
        job = Job(self.__namespace,
                  self.__job_config,
                  callbacks)
        job._Job__status.state = State.RUNNING

        @gen.coroutine
        def _stop(*args, **kwargs):
            pass

        @gen.coroutine
        def _delete(*args, **kwargs):
            pass

        @gen.coroutine
        def _delete_route(*args, **kwargs):
            pass

        @gen.coroutine
        def _status(*args, **kwargs):
            raise errors.CoordinatorNotExist()

        @gen.coroutine
        def _stop_previous_process(*args, **kwargs):
            pass

        fake_status.side_effect = _status
        fake_delete.side_effect = _delete
        fake_delete_route.side_effect = _delete_route
        mock_stop.side_effect = _stop
        mock_stop_previous_process.side_effect = _stop_previous_process

        ioloop.IOLoop.current().run_sync(job.stop)
        fake_delete.assert_called()
        self.assertEqual(fake_delete.call_count, 1)
        mock_db_callback.assert_called()
        self.assertEqual(mock_db_callback.call_count, 2)
        mock_finish_callback.assert_called()
        self.assertEqual(mock_finish_callback.call_count, 1)
        mock_stop.assert_not_called()
        mock_delete_callback.assert_not_called()
        mock_stop_previous_process.assert_called()

        self.assertEqual(job.status.state, State.STOPPED)

    def test_raise_exception_if_job_in_starting_operation_not_supported(self):
        callbacks = {"db_callback": fake_db_callback,
                     "delete_callback": fake_delete_callback,
                     "finish_callback": fake_finish_callback}
        job = Job(self.__namespace,
                  self.__job_config,
                  callbacks)
        job._Job__status.state = State.STARTING

        # operation start
        self.assertRaises(errors.JobSchedulerError,
                          job.assert_operation_valid, Operation.START)
        try:
            job.assert_operation_valid(Operation.START)
        except errors.JobSchedulerError as error:
            self.assertEqual(str(error),
                             "Namespace: test, job id: job1 in state: "
                             "STARTING, can not do operation: START.")

        # operation update
        self.assertRaises(errors.JobSchedulerError,
                          job.assert_operation_valid, Operation.UPDATE)
        try:
            job.assert_operation_valid(Operation.UPDATE)
        except errors.JobSchedulerError as error:
            self.assertEqual(str(error),
                             "Namespace: test, job id: job1 in state: "
                             "STARTING, can not do operation: UPDATE.")

    def test_raise_exception_if_job_in_running_operation_not_supported(self):
        callbacks = {"db_callback": fake_db_callback,
                     "delete_callback": fake_delete_callback,
                     "finish_callback": fake_finish_callback}
        job = Job(self.__namespace,
                  self.__job_config,
                  callbacks)
        job._Job__status.state = State.RUNNING

        # operation start
        self.assertRaises(errors.JobSchedulerError,
                          job.assert_operation_valid, Operation.START)
        try:
            job.assert_operation_valid(Operation.START)
        except errors.JobSchedulerError as error:
            self.assertEqual(str(error),
                             "Namespace: test, job id: job1 in state: "
                             "RUNNING, can not do operation: START.")

        # operation update
        self.assertRaises(errors.JobSchedulerError,
                          job.assert_operation_valid, Operation.UPDATE)
        try:
            job.assert_operation_valid(Operation.UPDATE)
        except errors.JobSchedulerError as error:
            self.assertEqual(str(error),
                             "Namespace: test, job id: job1 in state: "
                             "RUNNING, can not do operation: UPDATE.")

    def test_raise_exception_if_job_in_stopping_operation_not_supported(self):
        callbacks = {"db_callback": fake_db_callback,
                     "delete_callback": fake_delete_callback,
                     "finish_callback": fake_finish_callback}
        job = Job(self.__namespace,
                  self.__job_config,
                  callbacks)
        job._Job__status.state = State.STOPPING

        # operation update
        self.assertRaises(errors.JobSchedulerError,
                          job.assert_operation_valid, Operation.UPDATE)
        try:
            job.assert_operation_valid(Operation.UPDATE)
        except errors.JobSchedulerError as error:
            self.assertEqual(str(error),
                             "Namespace: test, job id: job1 in state: "
                             "STOPPING, can not do operation: UPDATE.")

        # operation stop
        self.assertRaises(errors.JobSchedulerError,
                          job.assert_operation_valid, Operation.STOP)
        try:
            job.assert_operation_valid(Operation.STOP)
        except errors.JobSchedulerError as error:
            self.assertEqual(str(error),
                             "Namespace: test, job id: job1 in state: "
                             "STOPPING, can not do operation: STOP.")

    def test_raise_exception_if_job_in_stopped_operation_not_supported(self):
        callbacks = {"db_callback": fake_db_callback,
                     "delete_callback": fake_delete_callback,
                     "finish_callback": fake_finish_callback}
        job = Job(self.__namespace,
                  self.__job_config,
                  callbacks)
        job._Job__status.state = State.STOPPED

        # operation stop
        self.assertRaises(errors.JobSchedulerError,
                          job.assert_operation_valid, Operation.STOP)
        try:
            job.assert_operation_valid(Operation.STOP)
        except errors.JobSchedulerError as error:
            self.assertEqual(str(error),
                             "Namespace: test, job id: job1 in state: "
                             "STOPPED, can not do operation: STOP.")

    def test_raise_exception_if_job_in_deleting_operation_not_supported(self):
        callbacks = {"db_callback": fake_db_callback,
                     "delete_callback": fake_delete_callback,
                     "finish_callback": fake_finish_callback}
        job = Job(self.__namespace,
                  self.__job_config,
                  callbacks)
        job._Job__status.state = State.DELETING

        # operation start
        self.assertRaises(errors.JobSchedulerError,
                          job.assert_operation_valid, Operation.START)
        try:
            job.assert_operation_valid(Operation.START)
        except errors.JobSchedulerError as error:
            self.assertEqual(str(error),
                             "Namespace: test, job id: job1 in state: "
                             "DELETING, can not do operation: START.")

        # operation update
        self.assertRaises(errors.JobSchedulerError,
                          job.assert_operation_valid, Operation.UPDATE)
        try:
            job.assert_operation_valid(Operation.UPDATE)
        except errors.JobSchedulerError as error:
            self.assertEqual(str(error),
                             "Namespace: test, job id: job1 in state: "
                             "DELETING, can not do operation: UPDATE.")

        # operation stop
        self.assertRaises(errors.JobSchedulerError,
                          job.assert_operation_valid, Operation.STOP)
        try:
            job.assert_operation_valid(Operation.STOP)
        except errors.JobSchedulerError as error:
            self.assertEqual(str(error),
                             "Namespace: test, job id: job1 in state: "
                             "DELETING, can not do operation: STOP.")

        # operation delete
        self.assertRaises(errors.JobSchedulerError,
                          job.assert_operation_valid, Operation.DELETE)
        try:
            job.assert_operation_valid(Operation.DELETE)
        except errors.JobSchedulerError as error:
            self.assertEqual(str(error),
                             "Namespace: test, job id: job1 in state: "
                             "DELETING, can not do operation: DELETE.")

#     def test_raise_exception_if_job_in_failed_operation_not_supported(self):
#         callbacks = {"db_callback": fake_db_callback,
#                      "delete_callback": fake_delete_callback,
#                      "finish_callback": fake_finish_callback}
#         job = Job(self.__namespace,
#                   self.__job_config,
#                   callbacks)
#         job._Job__status.state = State.FAILED
#
#         # operation stop
#         self.assertRaises(errors.JobSchedulerError,
#                           job.assert_operation_valid, Operation.STOP)
#         try:
#             job.assert_operation_valid(Operation.STOP)
#         except errors.JobSchedulerError as error:
#             self.assertEqual(str(error),
#                              "Namespace: test, job id: job1 in state: "
#                              "FAILED, can not do operation: STOP.")

    def test_raise_exception_if_job_in_finished_operation_not_supported(self):
        callbacks = {"db_callback": fake_db_callback,
                     "delete_callback": fake_delete_callback,
                     "finish_callback": fake_finish_callback}
        job = Job(self.__namespace,
                  self.__job_config,
                  callbacks)
        job._Job__status.state = State.FINISHED

        # operation stop
        self.assertRaises(errors.JobSchedulerError,
                          job.assert_operation_valid, Operation.STOP)
        try:
            job.assert_operation_valid(Operation.STOP)
        except errors.JobSchedulerError as error:
            self.assertEqual(str(error),
                             "Namespace: test, job id: job1 in state: "
                             "FINISHED, can not do operation: STOP.")

    def test_raise_exception_if_job_in_queuing_operation_not_supported(self):
        callbacks = {"db_callback": fake_db_callback,
                     "delete_callback": fake_delete_callback,
                     "finish_callback": fake_finish_callback}
        job = Job(self.__namespace,
                  self.__job_config,
                  callbacks)
        job._Job__status.state = State.QUEUING

        # operation start
        self.assertRaises(errors.JobSchedulerError,
                          job.assert_operation_valid, Operation.START)
        try:
            job.assert_operation_valid(Operation.START)
        except errors.JobSchedulerError as error:
            self.assertEqual(str(error),
                             "Namespace: test, job id: job1 in state: "
                             "QUEUING, can not do operation: START.")

    def test_reset_start_time_successfully(self):
        callbacks = {"db_callback": fake_db_callback,
                     "delete_callback": fake_delete_callback,
                     "finish_callback": fake_finish_callback}
        job = Job(self.__namespace,
                  self.__job_config,
                  callbacks)

        time.sleep(1)
        job.reset_start_time()

        self.assertTrue(
            job.to_dict()["start_time"] > job.to_dict()["create_time"])


if __name__ == '__main__':
    unittest.main()
