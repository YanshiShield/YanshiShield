#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint: disable=missing-function-docstring
"""FT for TASK."""
import logging
import unittest
from time import sleep
from tornado import gen, ioloop

from neursafe_fl.python.libs.cloud.task import TASK, TaskNotExist, TaskGetFailed, TaskExisted, \
    TaskCreateFailed
from neursafe_fl.python.utils.log import set_buildin_log


set_buildin_log()


def assert_task_create_succ(value):
    logging.debug(value)


def assert_task_delete_succ(value):
    logging.debug(value)


class TaskTest(unittest.TestCase):
    """
    Cases:
        test_k8s_task_create_succ
        test_k8s_task_create_failed_when_task_exists
        test_k8s_task_delete_succ
        test_k8s_task_delete_failed_when_task_unexist
        test_k8s_task_get_succ
        test_k8s_task_get_failed_when_task_unexist
    """

    def setUp(self):
        self.__task = TASK

    def tearDown(self):
        logging.info('tearDown')
        ioloop.IOLoop.current().run_sync(self.__delete_task_by_ignore_error)
        ioloop.IOLoop.current().run_sync(self.__wait_task_delete_finished)

    @gen.coroutine
    def __wait_task_delete_finished(self):
        logging.info('Task Waiting start...')
        try:
            max_times = 100
            times = 0
            while times < max_times:
                yield self.__get_task()

                sleep(0.5)
                times += 1
                logging.info('Task still exists. Waiting...')
        except (TaskNotExist, TaskGetFailed):
            pass

    def test_k8s_task_create_succ(self):
        @gen.coroutine
        def test():
            result = yield self.__create_task()
            logging.debug(result)
            assert_task_create_succ(result)
            sleep(1)

        ioloop.IOLoop.current().run_sync(test)

    def test_k8s_task_create_failed_when_task_exists(self):
        @gen.coroutine
        def test():
            yield self.__create_task()
            sleep(1)

            with self.assertRaises(TaskExisted):
                yield self.__create_task()

            with self.assertRaises(TaskCreateFailed):
                yield self.__create_task()

        ioloop.IOLoop.current().run_sync(test)

    def test_k8s_task_delete_succ(self):
        @gen.coroutine
        def test():
            yield self.__create_task()
            sleep(0.5)

            result = yield self.__delete_task()
            assert_task_delete_succ(result)

        ioloop.IOLoop.current().run_sync(test)

    def test_k8s_task_delete_failed_when_task_unexist(self):
        @gen.coroutine
        def test():
            with self.assertRaises(TaskNotExist):
                yield self.__delete_task()

        ioloop.IOLoop.current().run_sync(test)

    def test_k8s_task_get_succ(self):
        def assert_return_value_is_task(value):
            self.assertTrue('image' in value)
            self.assertTrue('state' in value)

        @gen.coroutine
        def test():
            yield self.__create_task()
            sleep(2)

            result = yield self.__get_task()
            assert_return_value_is_task(result)

        ioloop.IOLoop.current().run_sync(test)

    def test_k8s_task_get_failed_when_task_unexist(self):
        @gen.coroutine
        def test():
            with self.assertRaises(TaskNotExist):
                yield self.__get_task()

        ioloop.IOLoop.current().run_sync(test)

    @gen.coroutine
    def __create_task(self):
        task = yield self.__task.create(**get_task_cfg())
        raise gen.Return(task)

    @gen.coroutine
    def __get_task(self):
        task = yield self.__task.get(
            get_task_cfg()['name'],
            get_task_cfg()['namespace'])
        raise gen.Return(task)

    @gen.coroutine
    def __delete_task(self):
        task = yield self.__task.delete(
            get_task_cfg()['name'],
            get_task_cfg()['namespace'])
        raise gen.Return(task)

    @gen.coroutine
    def __delete_task_by_ignore_error(self):
        try:
            self.__delete_task()
        except Exception:  # pylint: disable=broad-except
            pass

    CASE_NAME = ('TaskTest.'
                 'test_k8s_task_create_succ')


def get_task_cfg():
    return {
        'name': 'test-task', 'namespace': 'default',
        'cmds': ['sleep', '3600'], 'port': 50051,
        'image': '10.67.134.35:5000/busybox:latest',
        'volumes': [
            ('startup_cfg_file_path', '/tmp/coordinator.json',
             '/tmp/coordinator.json')]}


if __name__ == '__main__':
    # import sys;sys.argv = ['', TaskTest.CASE_NAME]
    unittest.main(verbosity=2)
