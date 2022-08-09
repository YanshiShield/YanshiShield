"""Task DAO, used to save task metadata, and query history task.
"""
import json
import logging

import lmdb

from neursafe_fl.python.libs.db.db_factory import create_db, DBType
from neursafe_fl.python.libs.db.errors import CollectionNotExisting
from neursafe_fl.python.resource_manager import const


def create_task_dao(config):
    """used to create task dao with different database.
    """
    dao_map = {
        "lmdb": LmdbTaskDao,
        "postgre": PostgreTaskDao,
        "mongo": MongoTaskDao
    }
    try:
        dao = dao_map[config.get("type", "other")](**config)
        logging.info("Use database %s success.", config.get("type"))
        return dao
    except KeyError:
        return TaskDao()


class TaskDao:
    """Used to save task metadata.
    """
    def __init__(self, **_):
        pass

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

    def close(self):
        """Close database's connection.
        """


class LmdbTaskDao(TaskDao):
    """Save task used lmdb.

    Args:
        path: Path where LMDB saves data.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__env = lmdb.open(kwargs["path"], lock=False)

    def save(self, task):
        with self.__env.begin(write=True) as txn:
            txn.put(task["id"].encode(), json.dumps(task).encode())
        logging.info("Save task %s to db succcess", task["id"])

    def update(self, task):
        self.save(task)

    def get(self, task_id):
        with self.__env.begin() as txn:
            return json.loads(txn.get(task_id.encode()))

    def get_all(self):
        with self.__env.begin() as txn:
            for _, value in txn.cursor():
                yield json.loads(value)

    def close(self):
        """Close LMDB connection.
        """
        self.__env.close()


TASK_COLLECTION_NAME = "nsfl_task_metas"


class PostgreTaskDao(TaskDao):
    """Save task used Postgre.
    """
    def __init__(self, **_):
        super().__init__(**_)
        self._init_db_collection(DBType.POSTGRESQL)

    def _init_db_collection(self, db_type):
        _db = create_db(db_type, db_server=const.DB_ADDRESS,
                        db_name=const.DB_NAME, user=const.DB_USERNAME,
                        pass_word=const.DB_PASSWORD)
        try:
            self.__db_collection = _db.get_collection(TASK_COLLECTION_NAME)
        except CollectionNotExisting:
            self.__db_collection = _db.create_collection(TASK_COLLECTION_NAME,
                                                         ["id"])

    def save(self, task):
        self.__db_collection.insert(task)
        logging.info("Save task %s to db succcess", task["id"])

    def update(self, task):
        self.__db_collection.update({"id": task["id"]}, task)

    def get(self, task_id):
        self.__db_collection.find_one({"id": task_id})

    def get_all(self):
        return self.__db_collection.find_all()

    def close(self):
        pass


class MongoTaskDao(PostgreTaskDao):
    """Save task used mongo.
    """
    def __init__(self, **_):
        super().__init__(**_)
        self._init_db_collection(DBType.MONGO)
