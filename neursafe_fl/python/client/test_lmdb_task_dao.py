#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
# pylint:disable=missing-function-docstring
"""Test lmdb.
"""
import shutil
import tempfile
import unittest

from absl import logging

from neursafe_fl.python.client.task_dao import create_task_dao


class TestLMDBTaskDao(unittest.TestCase):
    """Test lmdb.
    """
    def setUp(self):
        self.__tempdir = tempfile.mktemp(prefix="lmdbtest")
        self.__lmdb = create_task_dao({"type": "lmdb", "path": self.__tempdir})

    def tearDown(self):
        self.__lmdb.close()
        logging.debug(self.__tempdir)
        shutil.rmtree(self.__tempdir)

    def test_should_write_and_read(self):
        task = {"id": "a1", "job_name": "aaa"}
        self.__lmdb.save(task)

        result = self.__lmdb.get("a1")
        self.assertEqual(result, task)

    def test_should_read_all(self):
        task1 = {"id": "a1", "job_name": "aaa"}
        task2 = {"id": "a2", "job_name": "aaaa"}
        self.__lmdb.save(task1)
        self.__lmdb.save(task2)

        for value in self.__lmdb.get_all():
            logging.info(value)

    def test_should_modify_when_write_same_key(self):
        task1 = {"id": "a3", "job_name": "aaa"}
        self.__lmdb.save(task1)
        result = self.__lmdb.get("a3")
        self.assertEqual(result, task1)

        task2 = {"id": "a3", "status": "bbb"}
        self.__lmdb.save(task2)
        result = self.__lmdb.get("a3")
        self.assertEqual(result, task2)


if __name__ == "__main__":
    unittest.main()
