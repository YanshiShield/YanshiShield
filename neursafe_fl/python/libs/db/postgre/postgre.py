#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint: disable=too-many-arguments
"""postgreSQL
"""
import json
from absl import logging

import psycopg2
import psycopg2.sql as psy_sql
from psycopg2 import errorcodes

from neursafe_fl.python.libs.db.base_db import DataBaseInterface,\
    CollectionInterface
from neursafe_fl.python.libs.db.postgre.errors import \
    UndefinedTable, UniqueViolation, DuplicateTable
import neursafe_fl.python.libs.db.errors as errors

CONNECTION_TIMEOUT = 10
DATA_COLUMN_NAME = "data"


def _convert_para_to_int(parameter):
    if isinstance(parameter, str):
        return int(parameter)

    return parameter


def _gen_sorts_key(sorts):
    if sorts:
        sort_keys_str = " ORDER BY "
        for sort in sorts:
            if sort.get("ascending", True):
                sort_key_str = "%s->>'%s' %s, " % (DATA_COLUMN_NAME,
                                                   sort["key"],
                                                   "ASC")
            else:
                sort_key_str = "%s->>'%s' %s, " % (DATA_COLUMN_NAME,
                                                   sort["key"],
                                                   "DESC")

            sort_keys_str += sort_key_str

        return sort_keys_str[:-2]

    return ""


def _gen_indexes_key(indexes):
    indexes_key_str = ""
    for index in indexes:
        index_key_str = "(%s->>'%s'), " % (DATA_COLUMN_NAME, index)
        indexes_key_str += index_key_str

    return indexes_key_str[:-2]


class PostgreClient:
    """PostgreSQL client
    """
    def __init__(self, db_host, db_port, db_name, user=None, pass_word=None):
        self.__db_host = db_host
        self.__db_port = _convert_para_to_int(db_port)
        self.__db_name = db_name
        self.__user = user
        self.__pass_word = pass_word

        self.__conn = None
        self.__cursor = None

    def connect(self):
        """connect to postgresql database
        """
        try:
            self.__conn = psycopg2.connect(host=self.__db_host,
                                           port=self.__db_port,
                                           user=self.__user,
                                           password=self.__pass_word,
                                           database=self.__db_name,
                                           connect_timeout=CONNECTION_TIMEOUT)
            self.__cursor = self.__conn.cursor()
        except psycopg2.Error as err:
            err_msg = "PostgreSQL create failed, error code: %s, error info:" \
                      " %s" % (err.pgcode, str(err))
            logging.exception(err_msg)
            raise errors.DataBaseError(err_msg)

    def execute(self, sql, params=None, **kwargs):
        """execute sql command
        """
        try:
            if not self.__conn or not self.__cursor:
                raise errors.DataBaseError("Please connect postsql first.")

            self.__cursor.execute(sql, params)
            if kwargs.get("commit", False):
                self.__conn.commit()
            if kwargs.get("fetchall", False):
                return self.__cursor.fetchall()
            if kwargs.get("fetchone", False):
                return self.__cursor.fetchone()
            if kwargs.get("rowcount", False):
                return self.__cursor.rowcount
            return None
        except psycopg2.Error as err:
            err_msg = "PostgreSQL execute sql: %s, params: %s failed, error " \
                      "code: %s, error info: %s" % (sql, params,
                                                    err.pgcode, str(err))
            logging.error(err_msg)
            self.__conn.rollback()

            if err.pgcode == errorcodes.DUPLICATE_TABLE:
                raise DuplicateTable() from err

            if err.pgcode == errorcodes.UNDEFINED_TABLE:
                raise UndefinedTable() from err

            if err.pgcode == errorcodes.UNIQUE_VIOLATION:
                raise UniqueViolation() from err

            raise errors.DataBaseError(str(err))


class PostgreSQL(DataBaseInterface):
    """postgreSQL data base
    """

    def __init__(self, db_server, db_name, user=None, pass_word=None):
        self.__db_name = db_name

        host, port = db_server.split(":")
        self.__client = PostgreClient(host, port, db_name, user, pass_word)

        self.__client.connect()

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
        try:
            create_table_sql = ("CREATE TABLE " + collection_name + " ("
                                "id serial PRIMARY KEY,"
                                "%s jsonb"
                                ");"
                                ) % DATA_COLUMN_NAME

            if indexes:
                create_index_sql = "CREATE UNIQUE INDEX ON %s (%s);" \
                                   % (collection_name,
                                      _gen_indexes_key(indexes))
                self.__client.execute(create_table_sql, commit=False)
                self.__client.execute(create_index_sql, commit=True)
            else:
                self.__client.execute(create_table_sql, commit=True)

            return Collection(collection_name, self.__client)
        except DuplicateTable as err:
            err_msg = "Collection %s already existing." % collection_name
            logging.error(err_msg)
            raise errors.CollectionAlreadyExisting(err_msg) from err

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
        sql = "SELECT table_name FROM information_schema.TABLES WHERE " \
              "table_name ='%s';" % collection_name
        result = self.__client.execute(sql, fetchone=True)
        if result:
            return Collection(collection_name, self.__client)

        err_msg = "Collection %s not existing." % collection_name
        raise errors.CollectionNotExisting(err_msg)

    def delete_collection(self, collection_name):
        """
        Delete collection in data base.

        Args:
            collection_name: which collection will be deleted.

        Raises:
            DataBaseError: if raise other data base exceptions.
        """
        try:
            sql = "DROP TABLE %s;" % collection_name
            self.__client.execute(sql, commit=True)
        except UndefinedTable:
            logging.warning("Collection: %s not existing.", collection_name)

    def drop(self):
        """
        Delete data base.

        Raises:
            DataBaseError: if raise other data base exceptions.
        """
        err_msg = "'DROP DATABASE' cannot be executed while anyone are " \
                  "connected to the target database."
        logging.error(err_msg)
        raise errors.DataBaseError(err_msg)


class Collection(CollectionInterface):
    """
    Collection implement
    """

    def __init__(self, name, postsql_client):
        self.__name = name
        self.__client = postsql_client

    def insert(self, data):
        """insert data

        Args:
            data: data to be added to collection.

        Raises:
            DataAlreadyExisting: if data already existing.
            DataBaseError: if raise other data base exceptions.
        """
        try:
            sql = psy_sql.SQL("INSERT INTO {0} ({1}) VALUES ({2});").format(
                psy_sql.Identifier(self.__name),
                psy_sql.Identifier(DATA_COLUMN_NAME),
                psy_sql.Literal(json.dumps(data)))
            return self.__client.execute(sql, commit=True, rowcount=True)
        except UniqueViolation as err:
            raise errors.DataAlreadyExisting(
                "Data already existing: %s" % data) from err

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
        sql = psy_sql.SQL(
            "UPDATE {0} SET {1} = {2} || {3} WHERE data @> {4};").format(
            psy_sql.Identifier(self.__name),
            psy_sql.Identifier(DATA_COLUMN_NAME),
            psy_sql.Identifier(DATA_COLUMN_NAME),
            psy_sql.Literal(json.dumps(data)),
            psy_sql.Literal(json.dumps(filters)))
        rowcount = self.__client.execute(sql, commit=True, rowcount=True)
        if rowcount == 0:
            err_msg = "Update failed, not matched data with filters: " \
                      "%s" % filters
            raise errors.DataNotExisting(err_msg)

    def replace(self, filters, data):
        """
        Replace specific data

        Args:
            filters: a dictionary specifying which query to be performed.
            data: data to be replaced to collection.

        Raises:
            DataBaseError: if raise other data base exceptions.
        """
        sql = psy_sql.SQL(
            "UPDATE {0} SET {1} = {2} WHERE data @> {3};").format(
            psy_sql.Identifier(self.__name),
            psy_sql.Identifier(DATA_COLUMN_NAME),
            psy_sql.Literal(json.dumps(data)),
            psy_sql.Literal(json.dumps(filters)))
        rowcount = self.__client.execute(sql, commit=True, rowcount=True)
        if rowcount == 0:
            err_msg = "Update failed, not matched data with filters: " \
                      "%s" % filters
            raise errors.DataNotExisting(err_msg)

    def delete(self, filters):
        """
        delete specific data

        Args:
            filters: a dictionary specifying which query to be performed.

        Raises:
            DataBaseError: if raise other data base exceptions.
        """
        sql = psy_sql.SQL("DELETE FROM {0} WHERE {1} @> {2};").format(
            psy_sql.Identifier(self.__name),
            psy_sql.Identifier(DATA_COLUMN_NAME),
            psy_sql.Literal(json.dumps(filters)))
        return self.__client.execute(sql, commit=True, rowcount=True)

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
        sql = psy_sql.SQL("SELECT {0} FROM {1} WHERE {2} @> {3};").format(
            psy_sql.Identifier(DATA_COLUMN_NAME),
            psy_sql.Identifier(self.__name),
            psy_sql.Identifier(DATA_COLUMN_NAME),
            psy_sql.Literal(json.dumps(filters)))
        result = self.__client.execute(sql, fetchone=True)
        if result:
            return result[0]

        raise errors.DataNotExisting(
            "Data not existing by filters: %s" % filters)

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
        sort_keys_str = _gen_sorts_key(sorts)

        if filters:
            sql = psy_sql.SQL("SELECT {0} FROM {1} WHERE {2} @> {3}%s;"
                              % sort_keys_str).format(
                psy_sql.Identifier(DATA_COLUMN_NAME),
                psy_sql.Identifier(self.__name),
                psy_sql.Identifier(DATA_COLUMN_NAME),
                psy_sql.Literal(json.dumps(filters)))
        else:
            sql = psy_sql.SQL("SELECT {0} FROM {1}%s;" % sort_keys_str).format(
                psy_sql.Identifier(DATA_COLUMN_NAME),
                psy_sql.Identifier(self.__name))

        result = self.__client.execute(sql, fetchall=True)

        if result:
            datas = []
            for data in result:
                datas.append(data[0])
            return iter(datas)

        raise errors.DataNotExisting(
            "Data not existing by filters: %s" % filters)

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
        sort_keys_str = _gen_sorts_key(sorts)

        sql = psy_sql.SQL("SELECT {0} FROM {1}%s" % sort_keys_str).format(
            psy_sql.Identifier(DATA_COLUMN_NAME),
            psy_sql.Identifier(self.__name))

        result = self.__client.execute(sql, fetchall=True)

        datas = []
        for data in result:
            datas.append(data[0])
        return iter(datas)
