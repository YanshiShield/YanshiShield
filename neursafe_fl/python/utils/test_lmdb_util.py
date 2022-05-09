#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=missing-function-docstring
"""Test lmdb.
"""
import json
import unittest
import tempfile
import shutil

from absl import logging
from neursafe_fl.python.utils import lmdb_util


class TestLMDB(unittest.TestCase):
    """Test lmdb.
    """
    def setUp(self):
        self.__tempdir = tempfile.mktemp(prefix="lmdbtest")
        self.__lmdb = lmdb_util.LMDBUtil(self.__tempdir)

    def tearDown(self):
        self.__lmdb.close()
        logging.debug(self.__tempdir)
        shutil.rmtree(self.__tempdir)

    def test_should_write_and_read(self):
        self.__lmdb.write("a1", "aaa")

        result = self.__lmdb.read("a1")
        self.assertEqual(result, "aaa")

    def test_should_write_and_read_dict(self):
        self.__lmdb.write("a2", json.dumps({"bb": 11}))

        result = json.loads(self.__lmdb.read("a2"))
        self.assertEqual(result, {"bb": 11})

    def test_should_read_all(self):
        self.__lmdb.write("aa", "aaa")
        self.__lmdb.write("a1", json.dumps({"bb": 11}))

        for key, value in self.__lmdb.read_all():
            logging.debug("%s %s", key, value)

    def test_should_modify_when_write_some_key(self):
        self.__lmdb.write("a3", json.dumps({"bb": 11}))
        result = json.loads(self.__lmdb.read("a3"))
        self.assertEqual(result, {"bb": 11})

        self.__lmdb.write("a3", json.dumps({"bb": 12}))
        result = json.loads(self.__lmdb.read("a3"))
        self.assertEqual(result, {"bb": 12})


if __name__ == "__main__":
    unittest.main()
