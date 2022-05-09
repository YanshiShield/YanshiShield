#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint: disable=missing-function-docstring
"""FT for kubernetes resource object."""
import logging
import unittest
from time import sleep
from tornado import gen, ioloop

from neursafe_fl.python.libs.cloud.const import K8S_ADDR
from neursafe_fl.python.libs.cloud.k8s_resource_object import K8sPod, PodNotExist, PodGetFailed, \
    K8sService, PodExisted, ServiceNotExist, ServiceExisted
from neursafe_fl.python.utils.log import set_buildin_log


set_buildin_log()


class K8sResourceObjectTest(unittest.TestCase):
    """
    Cases:
        test_create_service_success
        test_create_service_failed_when_service_exists
        test_get_service_succ
        test_get_service_failed_when_service_unexist
        test_delete_service_succ
        test_delete_service_failed_when_service_unexist

        test_create_pod_success
        test_create_pod_failed_when_pod_exists
        test_get_pod_succ
        test_get_pod_failed_when_pod_unexist
        test_delete_pod_succ
        test_delete_pod_failed_when_pod_unexist
        test_get_pod_failed_when_connect_failed
    """

    def setUp(self):
        logging.info('setUp')
        self.__pod = K8sPod(K8S_ADDR)
        self.__service = K8sService(K8S_ADDR)

    def tearDown(self):
        logging.info('tearDown')
        ioloop.IOLoop.current().run_sync(self.__wait_pod_delete_finished)
        ioloop.IOLoop.current().run_sync(self.__wait_service_delete_finished)

    # --service
    def test_create_service_success(self):
        def assert_return_value_is_service(value):
            self.assertTrue(value['kind'] == 'Service')

        @gen.coroutine
        def test():
            result = yield self.__create_service()
            logging.debug(result)
            assert_return_value_is_service(result)
            sleep(1)

            yield self.__delete_service()

        ioloop.IOLoop.current().run_sync(test)

    def test_create_service_failed_when_service_exists(self):
        @gen.coroutine
        def test():
            yield self.__create_service()
            sleep(1)

            with self.assertRaises(ServiceExisted):
                yield self.__create_service()

            yield self.__delete_service()

        ioloop.IOLoop.current().run_sync(test)

    def test_get_service_succ(self):
        def assert_return_value_is_service(value):
            self.assertTrue(value['kind'] == 'Service')

        @gen.coroutine
        def test():
            yield self.__create_service()
            sleep(1)

            result = yield self.__get_service()
            logging.debug(result)
            assert_return_value_is_service(result)

            yield self.__delete_service()

        ioloop.IOLoop.current().run_sync(test)

    def test_get_service_failed_when_service_unexist(self):
        @gen.coroutine
        def test():
            with self.assertRaises(ServiceNotExist):
                yield self.__get_service()

        ioloop.IOLoop.current().run_sync(test)

    def test_delete_service_succ(self):
        def assert_return_value_is_service_status(value):
            self.assertTrue(value['kind'] == 'Status')
            self.assertTrue(value['status'] == 'Success')

        @gen.coroutine
        def test():
            yield self.__create_service()
            sleep(0.5)

            result = yield self.__delete_service()
            logging.debug(result)
            assert_return_value_is_service_status(result)

        ioloop.IOLoop.current().run_sync(test)

    def test_delete_service_failed_when_service_unexist(self):
        @gen.coroutine
        def test():
            with self.assertRaises(ServiceNotExist):
                yield self.__delete_service()

        ioloop.IOLoop.current().run_sync(test)

    @gen.coroutine
    def __create_service(self):
        service = yield self.__service.create(get_service_cfg())
        raise gen.Return(service)

    @gen.coroutine
    def __get_service(self):
        service = yield self.__service.get(
            get_service_cfg()['metadata']['name'])
        raise gen.Return(service)

    @gen.coroutine
    def __delete_service(self):
        service = yield self.__service.delete(
            get_service_cfg()['metadata']['name'])
        raise gen.Return(service)

    # --pod
    def test_create_pod_success(self):
        def assert_return_value_is_pod(value):
            self.assertTrue('spec' in value)
            self.assertTrue('containers' in value['spec'])

        @gen.coroutine
        def test():
            result = yield self.__create_pod()
            assert_return_value_is_pod(result)
            sleep(2)

            yield self.__delete_pod()

        ioloop.IOLoop.current().run_sync(test)

    def test_create_pod_failed_when_pod_exists(self):
        @gen.coroutine
        def test():
            yield self.__create_pod()
            sleep(2)

            with self.assertRaises(PodExisted):
                yield self.__create_pod()

            yield self.__delete_pod()

        ioloop.IOLoop.current().run_sync(test)

    def test_get_pod_succ(self):
        def assert_return_value_is_pod(value):
            self.assertTrue('spec' in value)
            self.assertTrue('containers' in value['spec'])

        @gen.coroutine
        def test():
            yield self.__create_pod()
            sleep(3)

            result = yield self.__get_pod()
            assert_return_value_is_pod(result)

            yield self.__delete_pod()

        ioloop.IOLoop.current().run_sync(test)

    def test_get_pod_failed_when_pod_unexist(self):
        @gen.coroutine
        def test():
            with self.assertRaises(PodNotExist):
                yield self.__get_pod()

        ioloop.IOLoop.current().run_sync(test)

    def test_delete_pod_succ(self):
        def assert_return_value_is_pod(value):
            self.assertTrue('spec' in value)
            self.assertTrue('containers' in value['spec'])

        @gen.coroutine
        def test():
            yield self.__create_pod()
            sleep(0.5)

            result = yield self.__delete_pod()
            assert_return_value_is_pod(result)

        ioloop.IOLoop.current().run_sync(test)

    def test_delete_pod_failed_when_pod_unexist(self):
        @gen.coroutine
        def test():
            with self.assertRaises(PodNotExist):
                yield self.__delete_pod()

        ioloop.IOLoop.current().run_sync(test)

    @unittest.skip('')
    def test_get_pod_failed_when_connect_failed(self):
        @gen.coroutine
        def test():
            with self.assertRaises(PodGetFailed):
                yield K8sPod('10.67.134.15:111').get(
                    get_pod_cfg()['metadata']['name'],
                    get_pod_cfg()['metadata']['namespace'])

        ioloop.IOLoop.current().run_sync(test)

    @gen.coroutine
    def __create_pod(self):
        pod = yield self.__pod.create(get_pod_cfg())
        raise gen.Return(pod)

    @gen.coroutine
    def __get_pod(self):
        pod = yield self.__pod.get(
            get_pod_cfg()['metadata']['name'],
            get_pod_cfg()['metadata']['namespace'])
        raise gen.Return(pod)

    @gen.coroutine
    def __delete_pod(self):
        pod = yield self.__pod.delete(
            get_pod_cfg()['metadata']['name'],
            get_pod_cfg()['metadata']['namespace'])
        raise gen.Return(pod)

    CASE_NAME = ('K8sResourceObjectTest.'
                 'test_create_pod_success')

    @gen.coroutine
    def __wait_pod_delete_finished(self):
        logging.info('Pod Waiting start...')
        try:
            max_times = 100
            times = 0
            while times < max_times:
                yield self.__get_pod()

                sleep(1)
                times += 1
                logging.info('Pod still exists. Waiting...')
        except PodNotExist:
            pass

    @gen.coroutine
    def __wait_service_delete_finished(self):
        logging.info('Service Waiting start...')
        try:
            max_times = 100
            times = 0
            while times < max_times:
                yield self.__get_service()

                sleep(0.5)
                times += 1
                logging.info('Service still exists. Waiting...')
        except ServiceNotExist:
            pass


def get_pod_cfg():
    return {
        'kind': 'Pod',
        'apiVersion': 'v1',
        'metadata': {
            'name': 'test-task',
            'namespace': 'default',
            'labels': {
                'app': 'test-task'
            }
        },
        'spec': {
            'containers': [{
                'name': 'test-task',
                'image': '10.67.134.35:5000/busybox:latest',
                'command': ['sleep', '3600'],
                'resources': {},
                'imagePullPolicy': 'Never'
            }],
            'restartPolicy': 'Always',
            'nodeSelector': {
                'kubernetes.io/hostname': '10.67.134.15'
            }
        },
    }


def get_service_cfg():
    return {
        'apiVersion': 'v1',
        'kind': 'Service',
        'metadata': {
            'name': 'test'
        },
        'spec': {
            'selector': {
                'app': 'test'
            },
            'ports': [{
                'port': 50011,
                'targetPort': 50011
            }]
        }
    }


if __name__ == '__main__':
    # import sys;sys.argv = ['', K8sResourceObjectTest.CASE_NAME]
    unittest.main(verbosity=2)
