#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Store the model to Database.
"""

import time
from absl import logging
from neursafe_fl.python.model_manager.utils.tools import abnormal_exit
import neursafe_fl.python.model_manager.utils.const as const
import neursafe_fl.python.libs.db.errors as db_err
from neursafe_fl.python.libs.db.db_factory import create_db


def retry(func):
    """Define database retry wrapper.

    if connect db failed for several times, then will exit.
    """
    def wrapper(*args, **kwargs):
        try:
            retry_time = 0
            while retry_time <= const.RETRY_TIMES:
                try:
                    return func(*args, **kwargs)
                except db_err.DataBaseError as error:
                    logging.exception(str(error))
                    retry_time += 1
                    time.sleep(const.DB_RETRY_INTERVAL)
            raise RuntimeError

        except RuntimeError:
            err_msg = "Connect Database error, model manager exit."
            abnormal_exit(err_msg)

    return wrapper


class DBAdaptor:
    """Database interface for model persistence.
    """
    def __init__(self):
        self.__db = create_db(const.DB_TYPE,
                              db_server=const.DB_ADDRESS,
                              db_name=const.DB_NAME,
                              user=const.DB_USERNAME,
                              pass_word=const.DB_PASSWORD)

        self.__db_collection = self.__get_collection()

    @retry
    def __get_collection(self):
        """Create the collection if not exist.
        """
        try:
            collection = self.__db.get_collection(const.DB_COLLECTION_NAME)
        except db_err.CollectionNotExisting:
            collection = self.__db.create_collection(const.DB_COLLECTION_NAME,
                                                     indexes=["id"])
        return collection

    @retry
    def save(self, model):
        """Save model to database.
        """
        try:
            self.__db_collection.insert(model.to_dict())
        except db_err.DataAlreadyExisting:
            indexes = {"id": model.id}
            self.__db_collection.update(indexes, model.to_dict())

    @retry
    def update(self, model):
        """Update model info in database.
        """
        try:
            indexes = {"id": model.id}
            self.__db_collection.update(indexes, model.to_dict())
        except db_err.DataNotExisting:
            self.__db_collection.insert(model.to_dict())

    @retry
    def delete(self, model):
        """Delete model in database.
        """
        indexes = {"id": model.id}
        self.__db_collection.delete(indexes)

    @retry
    def read_all(self):
        """Read all the models in the database.
        """
        model_configs = self.__db_collection.find_all()
        return model_configs

    @retry
    def exist(self, model):
        """Check if model exist in database.
        """
        try:
            indexes = {"id": model.id}
            self.__db_collection.find_one(indexes)
            return True
        except db_err.DataNotExisting:
            return False
