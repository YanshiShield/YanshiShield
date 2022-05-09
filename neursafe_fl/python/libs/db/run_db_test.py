#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=missing-class-docstring, missing-function-docstring
# pylint:disable=too-many-public-methods
"""
data base exception definition
"""
import unittest

from neursafe_fl.python.libs.db.db_factory import create_db, DBType
from neursafe_fl.python.libs.db.base_db import CollectionInterface
import neursafe_fl.python.libs.db.errors as erros


class DBTest(unittest.TestCase):

    def setUp(self) -> None:
        # postgreSQL
        self.__db = create_db(DBType.POSTGRESQL,
                              db_server="10.67.134.32:12201",
                              db_name="jobs",
                              user="mytest",
                              pass_word="ZXCVasdf1234%")

        # mongo
        # self.__db = create_db(DBType.MONGO,
        #                       db_server="10.67.134.32:27017",
        #                       db_name="federated_learning",
        #                       user="root",
        #                       pass_word="1qaz2wsx(OL>")

        self.__collection_name = "test"
        self.__indexes = ['id', "name"]
        self.__sorts = [{"key": 'id', 'ascending': True},
                        {"key": 'name', 'ascending': False}]

        self.__db.create_collection(self.__collection_name, self.__indexes)

    def tearDown(self) -> None:
        self.__db.delete_collection(self.__collection_name)

    def __get_collection(self):
        return self.__db.get_collection(self.__collection_name)

    def test_raise_errors_if_db_type_not_support(self):
        self.assertRaises(erros.DataBaseError,
                          create_db,
                          "xxx")

    def test_create_collection_successfully(self):
        collection = self.__get_collection()

        self.assertTrue(isinstance(collection, CollectionInterface))

    def test_raise_errors_when_create_collection_if_collection_existing(self):
        self.assertRaises(erros.CollectionAlreadyExisting,
                          self.__db.create_collection,
                          self.__collection_name,
                          self.__indexes)

    def test_get_collection_successfully(self):
        collection = self.__get_collection()

        self.assertTrue(isinstance(collection, CollectionInterface))

    def test_raise_errors_when_get_collection_if_collection_not_existing(self):
        self.assertRaises(erros.CollectionNotExisting,
                          self.__db.get_collection,
                          "xxx")

    def test_insert_data_successfully(self):
        collection = self.__get_collection()
        data = {"id": "d1",
                "name": "n1"}
        collection.insert(data)

        res = collection.find_one({"id": "d1"})
        self.assertEqual(res, {"id": "d1",
                               "name": "n1"})

    def test_raise_errors_when_insert_data_if_data_index_existing(self):
        collection = self.__get_collection()
        data = {"id": "d1",
                "name": "n1"}
        collection.insert(data)

        self.assertRaises(erros.DataAlreadyExisting,
                          collection.insert,
                          data)

    def test_update_data_successfully(self):
        collection = self.__get_collection()
        data = {"id": "d1",
                "name": "n1"}
        collection.insert(data)

        collection.update({"id": "d1"}, {"apps": [1, 2]})

        res = collection.find_one({"id": "d1"})
        self.assertEqual(res, {"id": "d1",
                               "name": "n1",
                               "apps": [1, 2]})

    def test_raise_errors_when_update_if_data_not_existing(self):
        collection = self.__get_collection()
        self.assertRaises(erros.DataNotExisting,
                          collection.update,
                          {"id": "xxx"}, {"apps": None})

    def test_replace_data_successfully(self):
        collection = self.__get_collection()
        data = {"id": "d1",
                "name": "n1",
                "apps": [1, 2]}
        collection.insert(data)

        collection.replace({"id": "d1"}, {"id": "d1",
                                          "name": "n1"})

        res = collection.find_one({"id": "d1"})
        self.assertEqual(res, {"id": "d1",
                               "name": "n1"})

    def test_raise_errors_when_replace_if_data_not_existing(self):
        collection = self.__get_collection()
        self.assertRaises(erros.DataNotExisting,
                          collection.replace,
                          {"id": "xxx"}, {})

    def test_delete_data_successfully(self):
        collection = self.__get_collection()
        data = {"id": "d1",
                "name": "n1",
                "apps": [1, 2]}
        collection.insert(data)

        collection.delete({"id": "d1"})

        self.assertRaises(erros.DataNotExisting,
                          collection.find_one,
                          {"id": "d1"})

    def test_delete_no_existing_data(self):
        collection = self.__get_collection()
        collection.delete({"id": "d2"})

    def test_find_one_data_successfully(self):
        collection = self.__get_collection()
        data = {"id": "d1",
                "name": "n1"}
        collection.insert(data)

        res = collection.find_one({"id": "d1"})
        self.assertEqual(res, {"id": "d1",
                               "name": "n1"})

    def test_raise_errors_when_find_one_data_if_data_index_no_existing(self):
        collection = self.__get_collection()
        self.assertRaises(erros.DataNotExisting,
                          collection.find_one,
                          {"id": "xxx"})

    def test_find_data_successfully_and_return_data_in_specific_sort(self):
        data1 = {"id": "1",
                 "name": "n1",
                 "year": 20}
        data2 = {"id": "1",
                 "name": "n2",
                 "year": 21}
        data3 = {"id": "1",
                 "name": "n3",
                 "year": 22}
        data4 = {"id": "2",
                 "name": "n4",
                 "year": 23}

        collection = self.__get_collection()
        collection.insert(data1)
        collection.insert(data2)
        collection.insert(data3)
        collection.insert(data4)

        results = list(collection.find({"id": "1"}, self.__sorts))
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["name"], "n3")
        self.assertEqual(results[1]["name"], "n2")
        self.assertEqual(results[2]["name"], "n1")

    def test_raise_errors_when_find_data_if_data_index_no_existing(self):
        collection = self.__get_collection()
        self.assertRaises(erros.DataNotExisting,
                          collection.find,
                          {"id": "xxx"})

    def test_find_all_data_successfully_and_return_data_in_specific_sort(self):
        data1 = {"id": "1",
                 "name": "n1",
                 "year": 20}
        data2 = {"id": "1",
                 "name": "n2",
                 "year": 21}
        data3 = {"id": "2",
                 "name": "n3",
                 "year": 22}
        data4 = {"id": "2",
                 "name": "n4",
                 "year": 23}

        collection = self.__get_collection()
        collection.insert(data1)
        collection.insert(data2)
        collection.insert(data3)
        collection.insert(data4)

        results = list(collection.find_all(self.__sorts))
        self.assertEqual(len(results), 4)
        self.assertEqual(results[0]["id"], "1")
        self.assertEqual(results[0]["name"], "n2")
        self.assertEqual(results[1]["id"], "1")
        self.assertEqual(results[1]["name"], "n1")
        self.assertEqual(results[2]["id"], "2")
        self.assertEqual(results[2]["name"], "n4")
        self.assertEqual(results[3]["id"], "2")
        self.assertEqual(results[3]["name"], "n3")

    def test_find_all_data_if_collection_is_empty(self):
        collection = self.__get_collection()
        results = list(collection.find_all())

        self.assertEqual(results, [])


if __name__ == '__main__':
    unittest.main()
