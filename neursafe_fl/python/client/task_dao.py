#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Task DAO, used to save task metadata, and query history task.
"""
import logging

from neursafe_fl.python.libs.db.db_factory import create_db
from neursafe_fl.python.libs.db.errors import CollectionNotExisting
from neursafe_fl.python.resource_manager import const


TASK_COLLECTION_NAME = "nsfl_task_metas"


def create_task_dao(db_type):
    """used to create task dao with different database.
    """
    if db_type:
        return TaskDao(db_type)
    return BaseTaskDao()


class BaseTaskDao:
    """Used to save task metadata.
    """
    def save(self, task):
        """Save task metadata.
        """

    def update(self, task):
        """Update task metadata.
        """

    def get(self, task_id):
        """Get a task metadata with task id.
        """

    def get_all(self):
        """Get all task metadatas.
        """


class TaskDao(BaseTaskDao):
    """Save task used Postgre.
    """
    def __init__(self, db_type):
        _db = create_db(db_type, db_server=const.DB_ADDRESS,
                        db_name=const.DB_NAME, user=const.DB_USERNAME,
                        pass_word=const.DB_PASSWORD)
        try:
            self.__db_collection = _db.get_collection(TASK_COLLECTION_NAME)
        except CollectionNotExisting:
            self.__db_collection = _db.create_collection(TASK_COLLECTION_NAME,
                                                         ["id"])

    def save(self, task):
        """Save task metadata.
        """
        self.__db_collection.insert(task)
        logging.info("Save task %s to db succcess", task["id"])

    def update(self, task):
        """Update task metadata.
        """
        self.__db_collection.update({"id": task["id"]}, task)

    def get(self, task_id):
        """Get a task metadata with task id.
        """
        self.__db_collection.find_one({"id": task_id})

    def get_all(self):
        """Get all task metadatas.
        """
        return self.__db_collection.find_all()
