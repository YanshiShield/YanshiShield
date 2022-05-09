#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
abstract class of data base
"""

import abc


class DataBaseInterface(metaclass=abc.ABCMeta):
    """
    Data base interface class, inheritance class implement function.
    """

    @abc.abstractmethod
    def drop(self):
        """
        Delete data base.

        Raises:
            DBConnectError: if connect data base failed
            DataBaseError: if raise other data base exceptions.
        """

    @abc.abstractmethod
    def create_collection(self, collection_name, indexes=None):
        """
        Create collection, collection which belongs to one database will
        save specific data.

        Args:
            collection_name: which collection will be created.
            indexes: a single key or a list of (key, direction) pairs
                specifying the index as unique constraint,
                suc as ['name', 'age',...]

        Returns:
            Collection instance.

        Raises:
            CollectionAlreadyExisting: if collection already existing.
            DBConnectError: if connect data base failed.
            DataBaseError: if raise other data base exceptions.
        """

    @abc.abstractmethod
    def get_collection(self, collection_name):
        """
        Get collection.

        Args:
            collection_name: which collection will be gotten.

        Returns:
            Collection instance.

        Raises:
            CollectionNotExisting: if collection not existing.
            DBConnectError: if connect data base failed.
            DataBaseError: if raise other data base exceptions.
        """

    @abc.abstractmethod
    def delete_collection(self, collection_name):
        """
        Delete collection in data base.

        Args:
            collection_name: which collection will be deleted.

        Raises:
            DBConnectError: if connect data base failed.
            DataBaseError: if raise other data base exceptions.
        """


class CollectionInterface(metaclass=abc.ABCMeta):
    """
    Collection interface class, inheritance class implement function.

    collection do data adding, deleting, querying, updating operation. Its
    initialization parameters need specific bottom layer implementation of
    different types database, for example, if data base type is Mongo, the
    initialization parameter is specific collection instance of Mongo, if
    data base type is MySql, initialization parameter is specific table
    instance of MySql.
    """

    @abc.abstractmethod
    def insert(self, data):
        """insert data

        Args:
            data: data to be added to collection.

        Raises:
            DataAlreadyExisting: if data already existing.
            DBConnectError: if connect data base failed.
            DataBaseError: if raise other data base exceptions.
        """

    @abc.abstractmethod
    def find_one(self, filters):
        """
        Return one specific data according to querying condition.

        Args:
            filters: a dictionary specifying which query to be performed.

        Returns:
            data: specific data

        Raises:
            DataNotExisting: if data not existing.
            DBConnectError: if connect data base failed.
            DataBaseError: if raise other data base exceptions.
        """

    @abc.abstractmethod
    def find(self, filters, sorts=None):
        """
        Return all data according to querying condition.

        Args:
            filters: a dictionary specifying which query to be performed.
            sorts(optional): a list [{"key": $sort_key_1, "ascending": True},
                {"key": $sort_key_2, "ascending": True}] specify the sort order
                for this query; List element is a dict, "key" is required value,
                "ascending" is optional, default value is True; Smaller Element
                index of list means that the sort priority of element["key"] is
                higher.

        Returns:
            iter instance

        Raises:
            DBConnectError: if connect data base failed.
            DataBaseError: if raise other data base exceptions.
        """

    @abc.abstractmethod
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
            iter instance

        Raises:
            DBConnectError: if connect data base failed.
            DataBaseError: if raise other data base exceptions.
        """

    @abc.abstractmethod
    def update(self, filters, data):
        """
        Update specific data

        Args:
            filters: a dictionary specifying which query to be performed.
            data: data to be updated to collection.

        Raises:
            DataNotExisting: if data not existing.
            DBConnectError: if connect data base failed.
            DataBaseError: if raise other data base exceptions.
        """

    @abc.abstractmethod
    def replace(self, filters, data):
        """
        Replace specific data, update can update part data and replace will
        replace whole data.

        Args:
            filters: a dictionary specifying which query to be performed.
            data: data to be replaced to collection.

        Raises:
            DataBaseError: if raise other data base exceptions.
        """

    @abc.abstractmethod
    def delete(self, filters):
        """
        delete specific data

        Args:
            filters: a dictionary specifying which query to be performed.

        Raises:
            DBConnectError: if connect data base failed.
            DataBaseError: if raise other data base exceptions.
        """
