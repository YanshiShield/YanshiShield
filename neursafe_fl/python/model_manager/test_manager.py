#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=missing-function-docstring, invalid-name
"""Unittest for model manager.
"""
import unittest
import copy
import asyncio
import time
from mock import patch

from neursafe_fl.python.model_manager.manager import ModelManager
from neursafe_fl.python.model_manager.utils.db import DBAdaptor
from neursafe_fl.python.model_manager.model import Model
from neursafe_fl.python.model_manager.storage.storage_agent import StorageAgent,\
    StorageResponse
from neursafe_fl.python.model_manager.utils.errors import NotExist, ModelAlreadyExist, \
    ModelStateError


class FakeDB:
    """Mock of database.
    """

    def __init__(self, **kwargs):
        pass

    def read_all(self):
        pass

    def update(self, model):
        pass

    def save(self, model):
        pass

    def delete(self, model):
        pass

    def exist(self, model):
        pass


def fake_create():
    return None


def fake_delete(target, callback):
    del target
    time.sleep(2)
    result = StorageResponse(200, "success", None)
    callback(result)


class TestModelManager(unittest.TestCase):
    """Test cases of model manager.
    """

    @patch.object(StorageAgent, "__init__", FakeDB.__init__)
    @patch.object(DBAdaptor, "__init__", FakeDB.__init__)
    @patch.object(DBAdaptor, "read_all", FakeDB.read_all)
    def setUp(self) -> None:
        self.namespace = "test"
        self.config = {
            "name": "mnist",
            "runtime": "tensorflow"
        }
        self.model_manager = ModelManager()
        self.loop = asyncio.get_event_loop()

    @patch.object(Model, "create")
    def test_should_create_model_success_when_config_correct(self, mock_create):
        mock_create.side_effect = fake_create
        self.loop.run_until_complete(self.model_manager.create_model
                                     (self.namespace, self.config))
        mock_create.assert_called_once()

    def test_should_create_model_failed_when_config_error(self):
        config = copy.copy(self.config)
        del config["name"]
        with self.assertRaises(KeyError):
            self.loop.run_until_complete(self.model_manager.create_model
                                         (self.namespace, config))

        config = copy.copy(self.config)
        del config["runtime"]
        with self.assertRaises(ValueError):
            self.loop.run_until_complete(self.model_manager.create_model
                                         (self.namespace, config))

    @patch.object(Model, "create")
    def test_should_create_model_success_when_version_not_given(self,
                                                                mock_create):
        mock_create.side_effect = fake_create
        self.loop.run_until_complete(self.model_manager.create_model
                                     (self.namespace, self.config))
        mock_create.assert_called_once()

        model = self.model_manager.get_model(self.namespace,
                                             self.config["name"])
        self.assertIsNotNone(model)

    @patch.object(Model, "create")
    def test_should_create_model_success_when_version_given(self, mock_create):
        mock_create.side_effect = fake_create
        self.config["version"] = "latest"
        self.loop.run_until_complete(self.model_manager.create_model
                                     (self.namespace, self.config))
        mock_create.assert_called_once()

        model = self.model_manager.get_model(self.namespace,
                                             self.config["name"])
        self.assertIsNotNone(model)
        self.assertEqual(model[self.config["name"]][0]
                         ["version_info"].get("version"),
                         self.config["version"])

    @patch.object(Model, "create")
    def test_should_create_model_failed_when_version_already_exist(self,
                                                                   mock_create):
        mock_create.side_effect = fake_create
        self.config["version"] = "latest"
        self.loop.run_until_complete(self.model_manager.create_model
                                     (self.namespace, self.config))
        mock_create.assert_called_once()

        with self.assertRaises(ModelAlreadyExist):
            self.loop.run_until_complete(self.model_manager.create_model
                                         (self.namespace, self.config))

    @patch.object(Model, "create")
    def test_should_get_all_models_that_in_one_namespace(self, mock_create):
        config_1 = copy.copy(self.config)
        mock_create.side_effect = fake_create
        self.loop.run_until_complete(self.model_manager.create_model
                                     (self.namespace, config_1))

        config_2 = copy.copy(self.config)
        config_2["name"] = "flower"
        self.loop.run_until_complete(self.model_manager.create_model
                                     (self.namespace, config_2))

        models = self.model_manager.get_models(self.namespace)
        self.assertIsNotNone(models)
        self.assertIn(config_1["name"], models)
        self.assertIn(config_2["name"], models)

    @patch.object(Model, "create")
    def test_should_get_all_versions_of_model_success(self, mock_create):
        config_1 = copy.copy(self.config)
        config_1["version"] = "V10"
        mock_create.side_effect = fake_create
        self.loop.run_until_complete(self.model_manager.create_model
                                     (self.namespace, config_1))

        config_2 = copy.copy(self.config)
        config_2["version"] = "V20"
        self.loop.run_until_complete(self.model_manager.create_model
                                     (self.namespace, config_2))

        models = self.model_manager.get_model(self.namespace,
                                              self.config["name"])
        self.assertIsNotNone(models)
        models = models[self.config["name"]]
        versions = [models[0]["version_info"]["version"],
                    models[1]["version_info"]["version"]]
        self.assertIn(config_1["version"], versions)
        self.assertIn(config_2["version"], versions)

    @patch.object(Model, "create")
    def test_should_get_specified_version_of_model_success(self, mock_create):
        config_1 = copy.copy(self.config)
        config_1["version"] = "V10"
        mock_create.side_effect = fake_create
        self.loop.run_until_complete(self.model_manager.create_model
                                     (self.namespace, config_1))

        model = self.model_manager.get_model(self.namespace, config_1["name"],
                                             config_1["version"])
        self.assertIsNotNone(model)
        self.assertEqual(model[config_1["name"]][0]["version_info"]["version"],
                         config_1["version"])

    def test_should_get_model_failed_when_model_not_exist(self):
        with self.assertRaises(NotExist):
            self.model_manager.get_models(self.namespace)

        with self.assertRaises(NotExist):
            self.model_manager.get_model(self.namespace, self.config["name"])

    @patch.object(Model, "create")
    def test_should_get_model_failed_when_version_not_exist(self, mock_create):
        mock_create.side_effect = fake_create
        self.config["version"] = "latest"
        self.loop.run_until_complete(self.model_manager.create_model
                                     (self.namespace, self.config))

        with self.assertRaises(NotExist):
            self.model_manager.get_model(self.namespace, self.config["name"],
                                         version="Test")

    @patch.object(Model, "create")
    @patch.object(StorageAgent, "delete")
    @patch.object(DBAdaptor, "save", FakeDB.save)
    @patch.object(DBAdaptor, "delete", FakeDB.delete)
    @patch.object(DBAdaptor, "exist", FakeDB.exist)
    def test_should_delete_model_success(self, mock_delete, mock_create):
        mock_delete.side_effect = fake_delete
        mock_create.side_effect = fake_create
        self.loop.run_until_complete(self.model_manager.create_model
                                     (self.namespace, self.config))

        model = self.model_manager.get_model(self.namespace,
                                             self.config["name"])
        self.assertIsNotNone(model)
        with self.assertRaises(ModelStateError):
            self.loop.run_until_complete(self.model_manager.delete_model
                                         (self.namespace, self.config["name"]))

        self.model_manager.update_model({"state": "success", "progress": "100"},
                                        self.namespace, self.config["name"],
                                        model[self.config["name"]][0]
                                        ["version_info"]["version"])

        self.loop.run_until_complete(self.model_manager.delete_model
                                     (self.namespace, self.config["name"]))
        with self.assertRaises(NotExist):
            self.model_manager.get_model(self.namespace, self.config["name"])

    @patch.object(Model, "create")
    @patch.object(StorageAgent, "delete")
    @patch.object(DBAdaptor, "save", FakeDB.save)
    @patch.object(DBAdaptor, "delete", FakeDB.delete)
    @patch.object(DBAdaptor, "exist", FakeDB.exist)
    def test_should_delete_specified_version_of_model_success(self, mock_delete,
                                                              mock_create):
        mock_delete.side_effect = fake_delete
        mock_create.side_effect = fake_create
        self.config["version"] = "latest"
        self.loop.run_until_complete(self.model_manager.create_model
                                     (self.namespace, self.config))

        model = self.model_manager.get_model(self.namespace,
                                             self.config["name"],
                                             self.config["version"])
        self.assertIsNotNone(model)
        with self.assertRaises(ModelStateError):
            self.loop.run_until_complete(self.model_manager.delete_model
                                         (self.namespace, self.config["name"],
                                          self.config["version"]))

        self.model_manager.update_model({"state": "success", "progress": "100"},
                                        self.namespace, self.config["name"],
                                        self.config["version"])

        self.loop.run_until_complete(self.model_manager.delete_model
                                     (self.namespace, self.config["name"],
                                      self.config["version"]))
        with self.assertRaises(NotExist):
            self.model_manager.get_model(self.namespace, self.config["name"],
                                         self.config["version"])

    def test_should_delete_model_failed_when_model_not_exist(self):
        with self.assertRaises(NotExist):
            self.loop.run_until_complete(self.model_manager.delete_model
                                         (self.namespace, self.config["name"]))

        with self.assertRaises(NotExist):
            self.loop.run_until_complete(self.model_manager.delete_model
                                         (self.namespace, self.config["name"],
                                          version="latest"))

    @patch.object(Model, "create")
    def test_should_get_model_success_by_id(self, mock_create):
        mock_create.side_effect = fake_create
        self.loop.run_until_complete(self.model_manager.create_model
                                     (self.namespace, self.config))

        model = self.model_manager.get_model(self.namespace,
                                             self.config["name"])
        model_id = model[self.config["name"]][0]["id"]
        model_2 = self.model_manager.get_model_by_id(model_id)
        self.assertEqual(model[self.config["name"]][0], model_2)

    def test_should_get_model_failed_if_id_not_exist(self):
        with self.assertRaises(NotExist):
            self.model_manager.get_model_by_id(model_id="not_exist")

    @patch.object(Model, "create")
    @patch.object(StorageAgent, "delete")
    @patch.object(DBAdaptor, "save", FakeDB.save)
    @patch.object(DBAdaptor, "delete", FakeDB.delete)
    @patch.object(DBAdaptor, "exist", FakeDB.exist)
    def test_should_delete_model_success_by_id(self, mock_delete, mock_create):
        mock_delete.side_effect = fake_delete
        mock_create.side_effect = fake_create
        self.loop.run_until_complete(self.model_manager.create_model
                                     (self.namespace, self.config))

        model = self.model_manager.get_model(self.namespace,
                                             self.config["name"])
        model_id = model[self.config["name"]][0]["id"]

        self.model_manager.update_model({"state": "success", "progress": "100"},
                                        self.namespace, self.config["name"],
                                        self.config["version"])

        self.loop.run_until_complete(self.model_manager.delete_model_by_id
                                     (model_id))
        with self.assertRaises(NotExist):
            self.model_manager.get_model_by_id(model_id)

    def test_should_delete_model_failed_if_id_not_exist(self):
        with self.assertRaises(NotExist):
            self.loop.run_until_complete(self.model_manager.delete_model_by_id
                                         (model_id="not_exist"))


if __name__ == "__main__":
    unittest.main()
