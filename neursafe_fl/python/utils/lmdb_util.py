#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=missing-function-docstring
"""LMDB util.
"""
import lmdb


class LMDBUtil:
    """LMDB util.

    Args:
        path: LMDB configuration path, the data will be wrote to LMDB
        is saved under this path.
    """
    def __init__(self, path):
        self.__env = lmdb.open(path)

    def write(self, key, value):
        """Write {key: value} to LMDB.
        """
        if isinstance(key, str):
            key = key.encode()
        if isinstance(value, str):
            value = value.encode()
        with self.__env.begin(write=True) as txn:
            txn.put(key, value)

    def read(self, key):
        """Read the value related to the key from LMDB.
        """
        if isinstance(key, str):
            key = key.encode()
        with self.__env.begin() as txn:
            return txn.get(key).decode()

    def read_all(self):
        """Iterate all data in LMDB.
        """
        with self.__env.begin() as txn:
            for key, value in txn.cursor():
                yield key, value

    def close(self):
        """Close LMDB connection.
        """
        self.__env.close()
