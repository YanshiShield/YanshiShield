#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint: disable=missing-function-docstring,line-too-long
"""UT for task."""
import logging
import unittest
from mock.mock import patch
from tornado import gen, ioloop

from neursafe_fl.python.libs.cloud.k8s_resource_object import K8sService, K8sPod, PodExisted,\
    PodCreateFailed
from neursafe_fl.python.libs.cloud.task import TASK, TaskExisted, TaskCreateFailed
from neursafe_fl.python.utils.log import set_buildin_log


set_buildin_log()


@gen.coroutine
def _mock_method_for_pod_create_failed(*xargs, **wargs):
    logging.debug('%s\n%s', xargs, wargs)
    raise PodCreateFailed()


@gen.coroutine
def _mock_method_for_pod_create_exists(*xargs, **wargs):
    logging.debug('%s\n%s', xargs, wargs)
    raise PodExisted()


@gen.coroutine
def _mock_method_for_pod(*xargs, **wargs):
    logging.debug('%s\n%s', xargs, wargs)
    raise gen.Return(get_pod())


@gen.coroutine
def _mock_method_for_service(*xargs, **wargs):
    logging.debug(xargs)
    logging.debug(wargs)

    raise gen.Return()


class TestTask(unittest.TestCase):
    """Cases:
    test_k8s_task_create_succ:
    test_k8s_task_create_failed_when_pod_exists
    test_k8s_task_create_failed_when_service_exists
    test_k8s_task_create_failed_when_service_create_failed
    test_k8s_task_create_failed_when_pod_create_failed

    test_k8s_task_delete_succ_when_service_pod_exists
    test_k8s_task_delete_succ_when_service_unexist_and_pod_exists.
    test_k8s_task_delete_failed_when_service_unexist_and_pod_unexist
    test_k8s_task_delete_failed_when_service_exists_and_pod_unexist
    test_k8s_task_delete_failed_when_service_failed
    test_k8s_task_delete_failed_when_service_succ_and_pod_failed

    test_k8s_task_get_succ_when_service_pod_exists
    test_k8s_task_get_succ_when_service_unexist_and_pod_exists.
    test_k8s_task_get_failed_when_service_unexist_and_pod_unexist
    test_k8s_task_get_failed_when_service_exists_and_pod_unexist
    test_k8s_task_get_failed_when_service_failed
    test_k8s_task_get_failed_when_service_succ_and_pod_failed
    """

    def setUp(self):
        self.__task = TASK

    @patch.object(K8sService, 'create')
    @patch.object(K8sPod, 'create')
    def test_k8s_task_create_succ(self, mock_pod_create, mock_service_create):
        mock_pod_create.side_effect = _mock_method_for_pod
        mock_service_create.side_effect = _mock_method_for_service

        def assert_return_value_is_task(value):
            self.assertTrue('image' in value)
            self.assertTrue('state' in value)

        @gen.coroutine
        def test():
            value = yield self.__task.create(**get_task_cfg())
            assert_return_value_is_task(value)

        ioloop.IOLoop.current().run_sync(test)

    @patch.object(K8sService, 'create')
    @patch.object(K8sPod, 'create')
    def test_k8s_task_create_failed_when_pod_exists(self, mock_pod_create, mock_service_create):
        mock_pod_create.side_effect = _mock_method_for_pod_create_exists
        mock_service_create.side_effect = _mock_method_for_service

        @gen.coroutine
        def test():
            with self.assertRaises(TaskExisted):
                yield self.__task.create(**get_task_cfg())

        ioloop.IOLoop.current().run_sync(test)

    def test_k8s_task_create_failed_when_service_exists(self):
        """"""

    def test_k8s_task_create_failed_when_service_create_failed(self):
        """"""

    @patch.object(K8sService, 'create')
    @patch.object(K8sPod, 'create')
    def test_k8s_task_create_failed_when_pod_create_failed(self, mock_pod_create, mock_service_create):
        mock_pod_create.side_effect = _mock_method_for_pod_create_failed
        mock_service_create.side_effect = _mock_method_for_service

        @gen.coroutine
        def test():
            with self.assertRaises(TaskCreateFailed):
                yield self.__task.create(**get_task_cfg())

        ioloop.IOLoop.current().run_sync(test)

    def test_k8s_task_delete_succ_when_service_pod_exists(self):
        """Assert return value is Task object."""

    def test_k8s_task_delete_succ_when_service_unexist_and_pod_exists(self):
        """"""

    def test_k8s_task_delete_failed_when_service_unexist_and_pod_unexist(self):
        """"""

    def test_k8s_task_delete_failed_when_service_exists_and_pod_unexist(self):
        """"""

    def test_k8s_task_delete_failed_when_service_failed(self):
        """"""

    def test_k8s_task_delete_failed_when_service_succ_and_pod_failed(self):
        """"""

    @patch.object(K8sService, 'get')
    @patch.object(K8sPod, 'get')
    def test_k8s_task_get_succ_when_service_pod_exists(self, mock_pod_get, mock_service_get):
        mock_pod_get.side_effect = _mock_method_for_pod
        mock_service_get.side_effect = _mock_method_for_service

        def assert_return_value_is_task(value):
            self.assertTrue('image' in value)
            self.assertTrue('state' in value)

        @gen.coroutine
        def test():
            task = yield self.__task.get('name', 'fl')
            assert_return_value_is_task(task)

        ioloop.IOLoop.current().run_sync(test)

        mock_service_get.assert_called_once_with('name', 'fl')
        mock_pod_get.assert_called_once_with('name', 'fl')

    def test_k8s_task_get_succ_when_service_unexist_and_pod_exists(self):
        """"""

    def test_k8s_task_get_failed_when_service_unexist_and_pod_unexist(self):
        """"""

    def test_k8s_task_get_failed_when_service_exists_and_pod_unexist(self):
        """"""

    def test_k8s_task_get_failed_when_service_failed(self):
        """"""

    def test_k8s_task_get_failed_when_service_succ_and_pod_failed(self):
        """"""

    CASE_NAME = ('TestTask.'
                 'test_k8s_task_create_succ')


def get_task_cfg():
    return {'name': 'pytorch-mnist-job', 'namespace': 'fl',
            'cmds': ['python3.7', '-m', 'neursafe_fl.python.coordinator.app',
                     '/tmp/coordinator.json'], 'port': 50051,
            'envs': {'name1': 'value1', 'name2': 'value2'},
            'image': 'fl-coordinator:latest', 'volumes': [
                ('startup_cfg_file_path', '/tmp/coordinator.json',
                 '/tmp/coordinator.json', "pvc"),
                ('model_path', '/root/wl/fl/pytorch_mnist/init_weights.pth',
                 '/root/wl/fl/pytorch_mnist/init_weights.pth', "pvc"),
                ('scripts', '/root/wl/fl/pytorch_mnist',
                 '/root/wl/fl/pytorch_mnist', "pvc")]}


def get_pod():
    return {
        'apiVersion': 'v1',
        'kind': 'Pod',
        'metadata': {
            'name': 'pytorch-mnist-job',
            'namespace': 'fl',
            'labels': {
                'app': 'pytorch-mnist-job'
            }
        },
        'spec': {
            'restartPolicy': 'Never',
            'nodeSelector': {
                'kubernetes.io/hostname': '10.67.134.15'
            },
            'containers': [{
                'name': 'pytorch-mnist-job',
                'image': 'fl-coordinator:latest',
                'imagePullPolicy': 'Never',
                'ports': [{
                    'containerPort': 50051
                }],
                'resources': {
                    'requests': {}
                },
                'env': [],
                'volumeMounts': [{
                    'name': 'startup-cfg-file-path',
                    'mountPath': '/tmp/coordinator.json'
                }, {
                    'name': 'model-path',
                    'mountPath': '/root/wl/fl/pytorch_mnist/init_weights.pth'
                }, {
                    'name': 'scripts',
                    'mountPath': '/root/wl/fl/pytorch_mnist'
                }],
                'command': ['python3.7', '-m', 'neursafe_fl.python.coordinator.app', '/tmp/coordinator.json']
            }],
            'volumes': [{
                'name': 'startup-cfg-file-path',
                'hostPath': {
                    'path': '/tmp/coordinator.json'
                }
            }, {
                'name': 'model-path',
                'hostPath': {
                    'path': '/root/wl/fl/pytorch_mnist/init_weights.pth'
                }
            }, {
                'name': 'scripts',
                'hostPath': {
                    'path': '/root/wl/fl/pytorch_mnist'
                }
            }]
        },
        'status': {
            'phase': 'Running'
        }
    }


if __name__ == '__main__':
    # import sys;sys.argv = ['', TestTask.CASE_NAME]
    unittest.main(verbosity=2)
