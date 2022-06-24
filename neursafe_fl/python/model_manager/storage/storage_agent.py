#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-few-public-methods, broad-except
"""Storage backend adaptor.
"""
from collections import namedtuple
import threading
from absl import logging
from tornado.web import gen
import neursafe_fl.python.model_manager.utils.const as const
from neursafe_fl.python.model_manager.storage.s3_client import S3Client
from neursafe_fl.python.model_manager.storage.posix_client import PosixClient
from neursafe_fl.python.model_manager.storage.base_io import PathNotExist


class StorageType:
    """Support storage type.
    """
    S3 = "s3"
    POSIX = "posix"


StorageResponse = namedtuple("StorageResponse", "code, state, message")


def create_storage_agent():
    """Create the backend agent of storage.
    """
    if const.STORAGE_TYPE == StorageType.S3:
        storage_client = S3Client(access_key=const.STORAGE_ACCESS_KEY,
                                  secret_key=const.STORAGE_SECRET_KEY,
                                  endpoint=const.STORAGE_ENDPOINT)
    elif const.STORAGE_TYPE == StorageType.POSIX:
        storage_client = PosixClient(root_path=const.WORKSPACE)
    else:
        raise TypeError("Not support storage %s" % const.STORAGE_TYPE)

    return storage_client


class StorageAgent:
    """Adaptor for storage backend.
    """

    def __init__(self):
        self.__client = create_storage_agent()
        self.__type = const.STORAGE_TYPE

    @gen.coroutine
    def copy(self, src, target, callback):
        """Copy src to target of backend.
        """
        t_id = threading.Thread(target=self.__do_copy,
                                args=(src, target, callback, ))
        t_id.start()

    def __do_copy(self, src, target, callback):
        try:
            self.__client.copy(src, target)
            result = StorageResponse(200, "success", None)
        except PathNotExist:
            result = StorageResponse(404, "failed", "Not found src.")
        except Exception as error:
            logging.exception(str(error))
            result = StorageResponse(503, "failed", "Storage internal error.")

        callback(result)

    @gen.coroutine
    def delete(self, target, callback):
        """Delete the target of backend.
        """
        t_id = threading.Thread(target=self.__do_delete,
                                args=(target, callback, ))
        t_id.start()

    def __do_delete(self, target, callback):
        try:
            self.__client.delete(target)
            result = StorageResponse(200, "success", None)
        except PathNotExist:
            result = StorageResponse(404, "failed", "Not found.")
        except Exception as error:
            logging.exception(str(error))
            result = StorageResponse(503, "failed", "Storage internal error.")

        callback(result)
