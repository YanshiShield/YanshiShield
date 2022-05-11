#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=missing-function-docstring, invalid-name
"""Function test for storage manager.
"""
import logging
import os
from os.path import join, getsize
import shutil
import tempfile
from time import sleep
import unittest

from neursafe_fl.python.client.storage_manager import StorageManager, StorageInsufficient


logging.basicConfig(
    format=('[%(asctime)s] %(filename)s[line:%(lineno)d]'
            ' %(levelname)s: %(message)s'),
    level=logging.DEBUG)


class TestStorageManager(unittest.TestCase):  # pylint:disable=missing-class-docstring
    CASE_NAME = (
        'TestStorageManager.'
        'test_should_storage_manager_status_be_health_in_time_when_the_storage_drops_below_the_quota')

    def setUp(self):
        self.__monitor_path = tempfile.mktemp(prefix='storage_manager_test')
        os.mkdir(self.__monitor_path)

        self.__protected_path_names = []
        self.__quota = 4.4 * getsize_of_one_sub_tree()
        self.__num_of_health_tree = int(4.4 * 0.7)  # 3

        self.__manager = StorageManager(
            self.__monitor_path,
            self.__filename_is_cleanable,
            self.__quota / (1024 * 1024))

    def tearDown(self):
        self.__manager.stop()
        shutil.rmtree(self.__monitor_path)

    def __filename_is_cleanable(self, name):
        return name not in self.__protected_path_names

    def __set_protected_names(self, protected_num):
        self.__protected_path_names = [str(x) for x in range(protected_num)]
        logging.info('Protected paths: %s', self.__protected_path_names)

    def test_should_assert_no_raise_exception_when_storage_is_sufficient(self):
        self.__manager.start()
        self.__manager.assert_storage_sufficient()

    def test_should_assert_raise_exception_when_storage_is_insufficient(self):
        self.__manager.start()

        self.__set_protected_names(6)
        create_sub_trees(base_path=self.__monitor_path, tree_num=6)

        self.__wait_metadata_caching_finished()

        with self.assertRaises(StorageInsufficient):
            self.__manager.assert_storage_sufficient()

    def test_should_manager_not_clear_when_not_excceeded_quota(self):
        self.__manager.start()
        self.assertEqual(self.__manager.monitor.occupied_size, 0)

        create_sub_trees(base_path=self.__monitor_path, tree_num=3)

        self.__wait_metadata_caching_start_and_finished()

        self.__manager.assert_storage_sufficient()
        self.__assert_metadata_consistency(3)
        self.__assert_size_consistency()

    def test_should_manager_clear_be_accurate_when_excceeded_quota(self):
        self.__manager.start()
        self.__manager.assert_storage_sufficient()

        create_sub_trees(base_path=self.__monitor_path, tree_num=6)

        self.__wait_metadata_caching_start_and_finished()

        self.__manager.assert_storage_sufficient()
        self.__assert_metadata_consistency(6)
        self.__assert_size_consistency()

    def test_should_manager_clear_be_accurate_when_excceeded_quota_and_some_dir_uncleanable(self):
        self.__manager.start()
        self.__manager.assert_storage_sufficient()

        self.__protected_path_names = ['0']
        create_sub_trees(base_path=self.__monitor_path, tree_num=6)

        self.__wait_metadata_caching_start_and_finished()

        self.__manager.assert_storage_sufficient()

        self.__assert_metadata_consistency(6)
        self.__assert_size_consistency()

    def test_should_manager_clear_be_accurate_when_uncleanable_dir_excceeded_healthy_quota(self):
        self.__manager.start()
        self.__manager.assert_storage_sufficient()

        self.__set_protected_names(4)
        create_sub_trees(base_path=self.__monitor_path, tree_num=6)

        self.__wait_metadata_caching_start_and_finished()

        self.__manager.assert_storage_sufficient()

        self.__assert_metadata_consistency(6)
        self.__assert_size_consistency()

    def test_should_manager_clear_be_accurate_when_uncleanable_dir_excceeded_quota(self):
        self.__manager.start()
        self.__manager.assert_storage_sufficient()

        self.__set_protected_names(5)
        create_sub_trees(base_path=self.__monitor_path, tree_num=6)

        self.__wait_metadata_caching_start_and_finished()

        with self.assertRaises(StorageInsufficient):
            self.__manager.assert_storage_sufficient()

        self.__assert_metadata_consistency(6)
        self.__assert_size_consistency()

    def test_should_manager_be_known_the_dir_change_from_uncleanable_to_cleanable(self):
        self.__manager.start()
        self.__manager.assert_storage_sufficient()

        self.__set_protected_names(5)
        create_sub_trees(base_path=self.__monitor_path, tree_num=6)

        self.__wait_metadata_caching_start_and_finished()

        with self.assertRaises(StorageInsufficient):
            self.__manager.assert_storage_sufficient()

        moved_path = join(self.__monitor_path, self.__protected_path_names[0])
        shutil.move(moved_path, join(self.__monitor_path, 'xxx'))

        self.__wait_metadata_caching_start_and_finished()

        self.__assert_size_consistency()
        self.__manager.assert_storage_sufficient()

    def test_should_storage_manager_status_be_health_in_time_when_the_storage_drops_below_the_quota(self):
        self.__manager.start()
        self.__manager.assert_storage_sufficient()

        self.__set_protected_names(6)
        create_sub_trees(base_path=self.__monitor_path, tree_num=6)

        self.__wait_metadata_caching_start_and_finished()

        with self.assertRaises(StorageInsufficient):
            self.__manager.assert_storage_sufficient()

        for index in range(3):
            shutil.rmtree(join(self.__monitor_path, str(index)))

        self.__wait_metadata_caching_start_and_finished()

    def __calculate_remained_trees(self, init_tree_num):
        init_trees = [join(self.__monitor_path, str(index))
                      for index in range(init_tree_num)]

        # Calculate remained_trees_of_protected.
        remained_trees_of_protected = [
            join(self.__monitor_path, str(protected_path_name))
            for protected_path_name in self.__protected_path_names]

        # Calculate remained_trees_of_unprotected.
        remained_trees_num_of_protected = len(self.__protected_path_names)
        assert remained_trees_num_of_protected < init_tree_num
        remained_trees_num_of_unprotected = self.__num_of_health_tree - remained_trees_num_of_protected

        remained_trees_of_unprotected = []
        if remained_trees_num_of_unprotected > 0:
            for protected_path_name in self.__protected_path_names:
                abs_path = join(self.__monitor_path, protected_path_name)
                init_trees.remove(abs_path)
            remained_trees_of_unprotected = init_trees[-remained_trees_num_of_unprotected:]

        return remained_trees_of_protected + remained_trees_of_unprotected

    def __assert_metadata_consistency(self, init_tree_num):
        """Assert consistency, about cached file meta-information and
        actual file meta-information.
        """
        expected_sub_trees = self.__calculate_remained_trees(init_tree_num)

        actual_sub_trees = []
        for basename in os.listdir(self.__monitor_path):
            abs_path = os.path.join(self.__monitor_path, basename)
            actual_sub_trees.append(abs_path)
        logging.debug(actual_sub_trees)

        self.assertEqual(sorted(expected_sub_trees),
                         sorted(actual_sub_trees))

    def __assert_size_consistency(self):
        actual_size = calculate_dir_size(
            self.__monitor_path) - getsize(self.__monitor_path)
        logging.debug(self.__manager.monitor.metadatas)
        self.assertEqual(self.__manager.monitor.occupied_size, actual_size)

    def __wait_metadata_caching_start_and_finished(self):
        self.__wait_metadata_caching_start()
        self.__wait_metadata_caching_finished()

    def __wait_metadata_caching_start(self):
        """Wait for the manager to start caching files.

        By default, there are files in the monitoring directory.
        Judgment condition of start: occupied_size > 0
        Conditions to stop waiting: (Satisfy one of them.)
            1. Caching STARTED.
            2. Waiting timeout. (Maximum number of waits reached)

        Raises:
            TimeoutError: Waiting timeout.
        """
        interval = 0.1
        max_wait_times = 10
        wait_times = 0
        while True:
            if self.__manager.monitor.occupied_size > 0:
                logging.info('Caching started.')
                break
            logging.info('Caching not start.')

            if wait_times < max_wait_times:
                logging.info('Waiting(%dth time)...', wait_times + 1)
                sleep(interval)
                wait_times += 1
            else:
                logging.info('Waiting timeout.')
                raise TimeoutError('WAIT_METADATA_CACHING_START')

    def __wait_metadata_caching_finished(self):
        """Wait for the manager to caching files finished.

        Judgment condition of FINISHED: Continuously three times,
            captured the event queue is empty. Note: This judgment
            is not completely sufficient. In some scenarios,
            the judgment is wrong.
        Conditions to stop waiting: (Satisfy one of them.)
            1. Caching FINISHED.
            2. Waiting timeout. (Maximum number of waits reached)

        Raises:
            TimeoutError: Waiting timeout.
        """
        captrued_empty_times = 0

        def is_caching_finished():
            nonlocal captrued_empty_times
            if self.__manager.monitor.observer.event_queue.empty():
                captrued_empty_times += 1
                logging.info('Capture the empty queue for the %dth time.',
                             captrued_empty_times)
                return captrued_empty_times > 3
            logging.info('Event queue not empty.')
            captrued_empty_times = 0
            return False

        interval = 0.1
        max_wait_times = 10
        wait_times = 0
        while True:
            if is_caching_finished():
                logging.info('Caching finished.')
                break

            if wait_times < max_wait_times:
                logging.info('Waiting(%dth time)...', wait_times + 1)
                sleep(interval)
                wait_times += 1
            else:
                logging.info('Waiting timeout.')
                raise TimeoutError('WAIT_METADATA_CACHING_START')


def getsize_of_one_sub_tree():
    tmp_path = tempfile.mktemp(prefix='sub_tree')
    create_sub_tree(tmp_path)
    tree_size = calculate_dir_size(tmp_path)
    shutil.rmtree(tmp_path)
    return tree_size


def create_sub_trees(base_path, tree_num):
    for index in range(tree_num):
        sub_tree_base_path = join(base_path, str(index))
        create_sub_tree(sub_tree_base_path)
        sleep(0.01)  # Make the creation time different.
    logging.info('Create trees finished in %s.', base_path)


def create_sub_tree(base_path):
    def create_dir(path):
        os.makedirs(path)

    def create_file(path):
        with open(path, 'w') as file:
            file.write('test')

    create_dir(join(base_path, 'dir1/dir2'))
    create_file(join(base_path, 'file1'))
    create_file(join(base_path, 'file2'))
    create_file(join(base_path, 'dir1/file3'))
    create_file(join(base_path, 'dir1/dir2/file4'))

    logging.info('Create tree(%s) finished.', base_path)


def calculate_dir_size(path):
    total_size = 0
    for root, _, files in os.walk(path):
        total_size += getsize(root)
        total_size += sum([getsize(join(root, name)) for name in files])
    return total_size


if __name__ == '__main__':
    #  import sys;sys.argv = ['', TestStorageManager.CASE_NAME]
    unittest.main(verbosity=2)
