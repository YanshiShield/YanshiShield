#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
mongo data base
"""

from absl import logging

from pymongo import MongoClient, ASCENDING, DESCENDING
import pymongo.errors as mongo_errors

from neursafe_fl.python.libs.db.base_db import DataBaseInterface, \
    CollectionInterface
import neursafe_fl.python.libs.db.errors as errors


def _gen_index_list(index_keys):
    """
    Generate index struct.
    """
    index_list = []
    for key in index_keys:
        index_list.append((key, ASCENDING))
    return index_list


class MongoDB(DataBaseInterface):
    """
    Mongo data base
    """

    def __init__(self, db_server, db_name, user=None, pass_word=None):
        try:
            self.__mongo_client = MongoClient(db_server)
            self.__db_name = db_name
            self.__db = self.__mongo_client[db_name]

            if user is not None:
                self.__auth_db(user, pass_word)
        except mongo_errors.PyMongoError as error:
            err_msg = 'fail to create or connect to database: %s, ' \
                      'error info: %s' % (self.__db_name, str(error))
            logging.exception(err_msg)
            raise errors.DataBaseError(err_msg)

    def __auth_db(self, user, pass_word):
        self.__db.authenticate(user, pass_word)

    def create_collection(self, collection_name, indexes=None):
        """
        Create collection

        Args:
            collection_name: which collection will be created.
            indexes: a single key or a list of (key, direction) pairs
                specifying the index as unique constraint,
                suc as ['name', 'age',...]

        Returns:
            Collection instance.

        Raises:
            CollectionAlreadyExisting: if collection already existing.
            DataBaseError: if raise other data base exceptions.
        """
        if collection_name in self.__db.list_collection_names():
            err_msg = "Collection %s already existing in db: %s." \
                      % (collection_name, self.__db_name)
            raise errors.CollectionAlreadyExisting(err_msg)

        try:
            collection = self.__db.create_collection(collection_name)
            if indexes:
                index_list = _gen_index_list(indexes)
                collection.create_index(index_list, unique=True)

            return Collection(collection)
        except mongo_errors.PyMongoError as error:
            err_msg = 'fail to create collection: %s in db: %s, error info: ' \
                      '%s' % (collection_name, self.__db_name, str(error))
            logging.exception(err_msg)
            raise errors.DataBaseError(err_msg)

    def get_collection(self, collection_name):
        """
        Get collection.

        Args:
            collection_name: which collection will be gotten.

        Returns:
            Collection instance.

        Raises:
            CollectionNotExisting: if collection not existing.
            DataBaseError: if raise other data base exceptions.
        """
        if collection_name not in self.__db.list_collection_names():
            err_msg = "Collection %s not existing in db: %s." \
                      % (collection_name, self.__db_name)
            raise errors.CollectionNotExisting(err_msg)

        try:
            collection = self.__db[collection_name]
            return Collection(collection)
        except mongo_errors.PyMongoError as error:
            err_msg = 'fail to get collection: %s in db: %s, error info: %s' \
                      % (collection_name, self.__db_name, str(error))
            logging.exception(err_msg)
            raise errors.DataBaseError(err_msg)

    def delete_collection(self, collection_name):
        """
        Delete collection in data base.

        Args:
            collection_name: which collection will be deleted.

        Raises:
            DataBaseError: if raise other data base exceptions.
        """
        try:
            self.__db.drop_collection(collection_name)
        except mongo_errors.PyMongoError as error:
            err_msg = 'fail to delete collection: %s in db: %s, error info: ' \
                      '%s' % (collection_name, self.__db_name, str(error))
            logging.exception(err_msg)
            raise errors.DataBaseError(err_msg)

    def drop(self):
        """
        Delete data base.

        Raises:
            DataBaseError: if raise other data base exceptions.
        """
        try:
            self.__mongo_client.drop_database(self.__db_name)
        except mongo_errors.PyMongoError as error:
            err_msg = 'fail to delete data base, error info: %s' % str(error)
            logging.exception(err_msg)
            raise errors.DataBaseError(err_msg)


class Collection(CollectionInterface):
    """
    Collection implement
    """

    def __init__(self, mongo_collection):
        self.__collection = mongo_collection

    def insert(self, data):
        """insert data

        Args:
            data: data to be added to collection.

        Raises:
            DataAlreadyExisting: if data already existing.
            DataBaseError: if raise other data base exceptions.
        """
        try:
            self.__collection.insert_one(data)
        except mongo_errors.DuplicateKeyError as error:
            logging.error(str(error))
            raise errors.DataAlreadyExisting("Data already existing: %s" % data)
        except mongo_errors.PyMongoError as error:
            err_msg = 'fail to insert data, error info: %s' % str(error)
            logging.exception(err_msg)
            raise errors.DataBaseError(err_msg)

    def update(self, filters, data):
        """
        Update specific data

        Args:
            filters: a dictionary specifying which query to be performed.
            data: data to be updated to collection.

        Raises:
            DataNotExisting: if data not existing.
            DataBaseError: if raise other data base exceptions.
        """
        try:
            result = self.__collection.update_one(filters, {"$set": data})
            if result.matched_count == 0:
                err_msg = "Update failed, not matched data with filters: " \
                          "%s" % filters
                raise errors.DataNotExisting(err_msg)
        except mongo_errors.PyMongoError as error:
            err_msg = 'fail to update data, error info: %s' % str(error)
            logging.exception(err_msg)
            raise errors.DataBaseError(err_msg)

    def replace(self, filters, data):
        """
        Replace specific data

        Args:
            filters: a dictionary specifying which query to be performed.
            data: data to be replaced to collection.

        Raises:
            DataBaseError: if raise other data base exceptions.
        """
        try:
            result = self.__collection.replace_one(filters, data)
            if result.matched_count == 0:
                err_msg = "Update failed, not matched data with filters: " \
                          "%s" % filters
                raise errors.DataNotExisting(err_msg)
        except mongo_errors.PyMongoError as error:
            err_msg = 'fail to update data, error info: %s' % str(error)
            logging.exception(err_msg)
            raise errors.DataBaseError(err_msg)

    def delete(self, filters):
        """
        delete specific data

        Args:
            filters: a dictionary specifying which query to be performed.

        Raises:
            DataBaseError: if raise other data base exceptions.
        """
        try:
            self.__collection.delete_many(filters)
        except mongo_errors.PyMongoError as error:
            err_msg = 'fail to delete data, error info: %s' % str(error)
            logging.exception(err_msg)
            raise errors.DataBaseError(err_msg)

    def find_one(self, filters):
        """
        Return one specific data according to querying condition.

        Args:
            filters: a dictionary specifying which query to be performed.

        Returns:
            data: specific data

        Raises:
            DataNotExisting: if data not existing.
            DataBaseError: if raise other data base exceptions.
        """
        try:
            res = self.__collection.find_one(filters,
                                             {'_id': False})

            if not res:
                raise errors.DataNotExisting(
                    "Data not existing by filters: %s" % filters)

            return res
        except mongo_errors.PyMongoError as error:
            err_msg = 'fail to fine one data, error info: %s' % str(error)
            logging.exception(err_msg)
            raise errors.DataBaseError(err_msg)

    def __gen_sort_key(self, sorts):
        if sorts:
            sort_keys = []
            for sort in sorts:
                is_ascending = sort.get("ascending", True)
                sort_keys.append((sort["key"],
                                  ASCENDING if is_ascending else DESCENDING))
            return sort_keys

        return None

    def find(self, filters=None, sorts=None):
        """
        Return all data according to querying condition.

        Args:
            filters(optional): a dictionary specifying which query to
                be performed.
            sorts(optional): a list [{"key": $sort_key_1, "ascending": True},
                {"key": $sort_key_2, "ascending": True}] specify the sort order
                for this query; List element is a dict, "key" is required value,
                "ascending" is optional, default value is True; Smaller Element
                index of list means that the sort priority of element["key"] is
                higher.

        Returns:
            an iterator instance.

        Raises:
            DataNotExisting: if data not existing.
            DataBaseError: if raise other data base exceptions.
        """
        try:
            res = self.__collection.find(filters,
                                         {'_id': False},
                                         sort=self.__gen_sort_key(sorts))

            if not res.count():
                raise errors.DataNotExisting(
                    "Data not existing by filters: %s" % filters)

            return res
        except mongo_errors.PyMongoError as error:
            err_msg = 'fail to find data, error info: %s' % str(error)
            logging.exception(err_msg)
            raise errors.DataBaseError(err_msg)

    def find_all(self, sorts=None):
        """
        Return all data of one collection

        Args:
            sorts(optional): a list [{"key": $sort_key_1, "ascending": True},
                {"key": $sort_key_2, "ascending": True}] specify the sort order
                for this query; List element is a dict, "key" is required value,
                "ascending" is optional, default value is True; Smaller Element
                index of list means that the sort priority of element["key"] is
                higher.

        Returns:
            an iterator instance.

        Raises:
            DataBaseError: if raise other data base exceptions.
        """
        try:
            return self.__collection.find({}, {'_id': False},
                                          sort=self.__gen_sort_key(sorts))
        except mongo_errors.PyMongoError as error:
            err_msg = 'fail to find data, error info: %s' % str(error)
            logging.exception(err_msg)
            raise errors.DataBaseError(err_msg)
