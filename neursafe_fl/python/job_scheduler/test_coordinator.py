#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint: disable=missing-function-docstring
"""Unit test for coordinator."""
import asyncio
import unittest
from mock import patch
from tornado import gen, ioloop

from neursafe_fl.python.job_scheduler.coordinator import Coordinator
from neursafe_fl.python.job_scheduler.util.errors import CoordinatorExists, \
    CoordinatorCreateFailed, CoordinatorNotExist, CoordinatorGetFailed, \
    CoordinatorDeleteFailed
from neursafe_fl.python.libs.cloud.task import TASK, TaskExisted, TaskCreateFailed, TaskNotExist, \
    TaskGetFailed, TaskDeleteFailed
from neursafe_fl.python.utils.log import set_buildin_log


set_buildin_log()


class TestCoordinator(unittest.TestCase):
    """
    Cases:
        test_create_succ
        test_create_failed_when_coor_exists
        test_create_failed_when_unknown_failed
        test_status_succ
        test_status_failed_when_coor_unexist
        test_status_failed_when_unknown_failed
        test_delete_succ
        test_delete_failed_when_coor_unexist
        test_delete_failed_unknown_failed
    """

    def setUp(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        self.__coordinator = Coordinator()

    @patch.object(TASK, "create")
    def test_create_succ(self, mock_task_create):
        @gen.coroutine
        def _mock_method(*xargs, **wargs):
            raise gen.Return({"state": "Running"})

        mock_task_create.side_effect = _mock_method

        @gen.coroutine
        def test():
            job_cfg = get_job_config()
            workspace = "/tmp"

            coor = yield self.__coordinator.create(job_cfg, workspace, "fl")
            self.assertEqual(coor, None)

        ioloop.IOLoop.current().run_sync(test)

        mock_task_create.assert_called_once_with(
            name="fl-pytorch-mnist-job",
            namespace="default",
            cmds=["python3.7", "-m",
                  "fl.python.coordinator.app", "--config_file",
                  "/tmp/job-id/coordinator.json"],
            port=50051, image="fl-coordinator:latest",
            volumes=get_volumes(),
            envs={"REPORT_PERIOD": "10",
                  "JOB_SCHEDULER_ADDRESS": "job-scheduler:8088",
                  "SELECTOR_ADDRESS": None,
                  'COORDINATOR_WORKSPACE_PATH': '/fl',
                  'DEPLOYMENT_WAY': 'cloud'})

    @patch.object(TASK, "create")
    def test_create_failed_when_coor_exists(self, mock_task_create):
        @gen.coroutine
        def _mock_method(*xargs, **wargs):
            raise TaskExisted()

        mock_task_create.side_effect = _mock_method

        @gen.coroutine
        def test():
            job_cfg = get_job_config()
            workspace = "/tmp"

            with self.assertRaises(CoordinatorExists):
                yield self.__coordinator.create(job_cfg, workspace)

        ioloop.IOLoop.current().run_sync(test)

    @patch.object(TASK, "create")
    def test_create_failed_when_unknown_failed(self, mock_task_create):
        @gen.coroutine
        def _mock_method(*xargs, **wargs):
            raise TaskCreateFailed()

        mock_task_create.side_effect = _mock_method

        @gen.coroutine
        def test():
            job_cfg = get_job_config()
            workspace = "/tmp"

            with self.assertRaises(CoordinatorCreateFailed):
                yield self.__coordinator.create(job_cfg, workspace)

        ioloop.IOLoop.current().run_sync(test)

    @patch.object(TASK, "get")
    def test_status_succ(self, mock_task_status):
        @gen.coroutine
        def _mock_method(*xargs, **wargs):
            raise gen.Return({"state": "Running"})

        mock_task_status.side_effect = _mock_method

        @gen.coroutine
        def test():
            coor = yield self.__coordinator.status("job_id", "fl")
            self.assertEqual(coor, {"state": "RUNNING"})

        ioloop.IOLoop.current().run_sync(test)

        mock_task_status.assert_called_once_with(
            name="fl-job_id",
            namespace="default")

    @patch.object(TASK, "get")
    def test_status_failed_when_coor_unexist(self, mock_task_status):
        @gen.coroutine
        def _mock_method(*xargs, **wargs):
            raise TaskNotExist()

        mock_task_status.side_effect = _mock_method

        @gen.coroutine
        def test():
            with self.assertRaises(CoordinatorNotExist):
                yield self.__coordinator.status("job_id")

        ioloop.IOLoop.current().run_sync(test)

    @patch.object(TASK, "get")
    def test_status_failed_when_unknown_failed(self, mock_task_status):
        @gen.coroutine
        def _mock_method(*xargs, **wargs):
            raise TaskGetFailed()

        mock_task_status.side_effect = _mock_method

        @gen.coroutine
        def test():
            with self.assertRaises(CoordinatorGetFailed):
                yield self.__coordinator.status("job_id")

        ioloop.IOLoop.current().run_sync(test)

    @patch.object(TASK, "delete")
    def test_delete_succ(self, mock_task_delete):
        @gen.coroutine
        def _mock_method(*xargs, **wargs):
            raise gen.Return({"state": "Running"})

        mock_task_delete.side_effect = _mock_method

        @gen.coroutine
        def test():
            coor = yield self.__coordinator.delete("job_id", "fl")
            self.assertEqual(coor, None)

        ioloop.IOLoop.current().run_sync(test)

        mock_task_delete.assert_called_once_with(
            name="fl-job_id",
            namespace="default")

    @patch.object(TASK, "delete")
    def test_delete_failed_when_coor_unexist(self, mock_task_delete):
        @gen.coroutine
        def _mock_method(*xargs, **wargs):
            raise TaskNotExist()

        mock_task_delete.side_effect = _mock_method

        @gen.coroutine
        def test():
            with self.assertRaises(CoordinatorNotExist):
                yield self.__coordinator.delete("job_id")

        ioloop.IOLoop.current().run_sync(test)

    @patch.object(TASK, "delete")
    def test_delete_failed_when_unknown_failed(self, mock_task_delete):
        @gen.coroutine
        def _mock_method(*xargs, **wargs):
            raise TaskDeleteFailed()

        mock_task_delete.side_effect = _mock_method

        @gen.coroutine
        def test():
            with self.assertRaises(CoordinatorDeleteFailed):
                yield self.__coordinator.delete("job_id")

        ioloop.IOLoop.current().run_sync(test)

    CASE_NAME = ("TestCoordinator."
                 "test_status_failed_when_unknown_failed")


def get_job_config():
    return {
        "id": "pytorch-mnist-job",
        "job-id": "job-id",
        "description": "example for federate learning",
        "clients": "fl-client:22000",
        "model_path": "/root/wl/fl/pytorch_mnist/init_weights.pth",
        "runtime": "pytorch",
        "scripts": {
            "path": "/root/wl/fl/pytorch_mnist",
            "config_file": "pytorch_mnist.json"
        },
        "output": "/root/wl/fl/pytorch_mnist",
        "hyper_parameters": {
            "max_round_num": 3,
            "min_client_num": 1,
            "evaluate_interval": 2,
            "model_save_policy": {
                "interval_round": 2
            }
        },
        "client_parameters": {
        },
        "port": 50051
    }


def get_volumes():
    return [("model-path",
             "/mnt/minio/fl/root/wl/fl/pytorch_mnist/init_weights.pth",
             "/fl/root/wl/fl/pytorch_mnist/init_weights.pth"),
            ("scripts", "/mnt/minio/fl/root/wl/fl/pytorch_mnist",
             "/fl/root/wl/fl/pytorch_mnist"),
            ('output', '/mnt/minio/fl/root/wl/fl/pytorch_mnist',
             '/fl/root/wl/fl/pytorch_mnist'),
            ('entrypoint', '/mnt/minio/tmp/job-id/coordinator.json',
             '/tmp/job-id/coordinator.json')]


if __name__ == "__main__":
    # import sys;sys.argv = ["", TestCoordinator.CASE_NAME]
    unittest.main(verbosity=2)
