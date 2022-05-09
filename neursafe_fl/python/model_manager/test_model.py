#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=missing-function-docstring, invalid-name
"""Unittest for model.
"""
import unittest
import asyncio
import copy

from neursafe_fl.python.model_manager.model import Model, ModelState
from neursafe_fl.python.model_manager.storage.storage_agent import StorageResponse
from neursafe_fl.python.model_manager.utils.const import HEARTBEAT_TIMEOUT
from neursafe_fl.python.model_manager.utils.errors import ModelStateError


class FakeDB:
    """Mock of database.
    """

    def __init__(self, **kwargs):
        pass

    def update(self, model):
        pass

    def save(self, model):
        pass

    def delete(self, model):
        pass

    def exist(self, model):
        pass


class FakeS3Agent:
    """Mock the s3 client with success response.
    """

    async def copy(self, src, target, callback):
        del src, target
        await asyncio.sleep(2)
        result = StorageResponse(200, "success", None)
        callback(result)

    async def delete(self, target, callback):
        del target
        await asyncio.sleep(2)
        result = StorageResponse(200, "success", None)
        callback(result)


class FakeFailedS3Agent:
    """Mock the s3 client with failed response.
    """

    async def copy(self, src, target, callback):
        del src, target
        await asyncio.sleep(2)
        result = StorageResponse(404, "failed", "not found")
        callback(result)

    async def delete(self, target, callback):
        del target
        await asyncio.sleep(2)
        result = StorageResponse(404, "failed", "not found")
        callback(result)


class TestModel(unittest.TestCase):
    """Test cases for model.
    """

    def setUp(self) -> None:
        self.db = FakeDB()
        self.s3_agent = FakeS3Agent()
        self.config = {
            "namespace": "test",
            "name": "mnist",
            "runtime": "tf",
            "version": "V1"
        }
        self.loop = asyncio.get_event_loop()

    def test_should_model_init_success_when_config_correct(self):
        model = Model(self.config, self.db, self.s3_agent)
        self.assertEqual(model.namespace, self.config["namespace"])
        self.assertEqual(model.name, self.config["name"])
        self.assertEqual(model.version, "V1")

    def test_should_model_init_failed_when_config_wrong(self):
        config = copy.copy(self.config)
        del config["namespace"]
        with self.assertRaises(Exception):
            Model(config, self.db, self.s3_agent)

        config = copy.copy(self.config)
        del config["name"]
        with self.assertRaises(Exception):
            Model(config, self.db, self.s3_agent)

        config = copy.copy(self.config)
        del config["runtime"]
        with self.assertRaises(Exception):
            Model(config, self.db, self.s3_agent)

        config = copy.copy(self.config)
        del config["version"]
        with self.assertRaises(Exception):
            Model(config, self.db, self.s3_agent)

    def test_should_model_create_success_with_local_file(self):
        model = Model(self.config, self.db, self.s3_agent)
        self.loop.run_until_complete(model.create())

        self.assertEqual(model.to_dict()["state"], ModelState.UNREADY)

        update_info = {"state": "success", "progress": "100"}
        model.update(update_info)
        self.assertEqual(model.to_dict()["state"], ModelState.READY)

    def test_should_model_create_failed_when_local_file_upload_failed(self):
        model = Model(self.config, self.db, self.s3_agent)
        self.loop.run_until_complete(model.create())

        self.assertEqual(model.to_dict()["state"], ModelState.UNREADY)

        update_info = {"state": "failed", "progress": "0"}
        model.update(update_info)
        self.assertEqual(model.to_dict()["state"], ModelState.ERROR)

    def test_should_model_create_failed_when_local_file_upload_timeout(self):
        model = Model(self.config, self.db, self.s3_agent)
        self.loop.run_until_complete(model.create())

        self.assertEqual(model.to_dict()["state"], ModelState.UNREADY)
        self.loop.run_until_complete(asyncio.sleep(HEARTBEAT_TIMEOUT))

        self.assertEqual(model.to_dict()["state"], ModelState.ERROR)

    def test_should_model_create_success_with_cloud_file(self):
        self.config["model_path"] = "default:/tmp/mnist.h5"
        model = Model(self.config, self.db, self.s3_agent)
        self.loop.run_until_complete(model.create())

        self.assertEqual(model.to_dict()["state"], ModelState.READY)

    def test_should_model_create_failed_when_cloud_file_not_exist(self):
        self.config["model_path"] = "default:/tmp/mnist.h5"
        failed_s3_agent = FakeFailedS3Agent()
        model = Model(self.config, self.db, failed_s3_agent)
        self.loop.run_until_complete(model.create())

        self.assertEqual(model.to_dict()["state"], ModelState.ERROR)

    def test_should_model_delete_success(self):
        def delete_callback(delete_model):
            self.assertEqual(delete_model.namespace, self.config["namespace"])
            self.assertEqual(delete_model.name, self.config["name"])
            self.assertEqual(delete_model.version, self.config["version"])

        callbacks = {"on_delete_finish": delete_callback}
        model = Model(self.config, self.db, self.s3_agent, callbacks=callbacks)
        self.loop.run_until_complete(model.create())

        self.assertEqual(model.to_dict()["state"], ModelState.UNREADY)

        update_info = {"state": "success", "progress": "100"}
        model.update(update_info)
        self.assertEqual(model.to_dict()["state"], ModelState.READY)
        self.loop.run_until_complete(model.delete())

    def test_should_model_delete_failed_when_already_in_deleting(self):
        model = Model(self.config, self.db, self.s3_agent)
        self.loop.run_until_complete(model.create())

        self.assertEqual(model.to_dict()["state"], ModelState.UNREADY)
        update_info = {"state": "success", "progress": "100"}
        model.update(update_info)
        self.assertEqual(model.to_dict()["state"], ModelState.READY)

        self.loop.run_until_complete(model.delete())
        self.assertEqual(model.to_dict()["state"], ModelState.DELETING)

        with self.assertRaises(ModelStateError):
            self.loop.run_until_complete(model.delete())

    def test_should_model_delete_failed_when_model_still_unready(self):
        model = Model(self.config, self.db, self.s3_agent)
        self.loop.run_until_complete(model.create())

        self.assertEqual(model.to_dict()["state"], ModelState.UNREADY)
        with self.assertRaises(ModelStateError):
            self.loop.run_until_complete(model.delete())

    def test_should_restore_model_success_when_state_unready_with_local_file(
            self):
        model = Model(self.config, self.db, self.s3_agent)
        self.loop.run_until_complete(model.create())

        self.assertEqual(model.to_dict()["state"], ModelState.UNREADY)
        model_dict = model.to_dict()

        restore_model = Model(model_dict, self.db, self.s3_agent)
        self.loop.run_until_complete(restore_model.restore())

        update_info = {"state": "success", "progress": "100"}
        model.update(update_info)
        self.assertEqual(model.to_dict()["state"], ModelState.READY)

    def test_should_restore_model_success_when_state_unready_with_cloud_file(
            self):
        self.config["model_path"] = "default:/tmp/mnist.h5"
        model = Model(self.config, self.db, self.s3_agent)
        self.assertEqual(model.to_dict()["state"], ModelState.UNREADY)
        model_dict = model.to_dict()

        restore_model = Model(model_dict, self.db, self.s3_agent)
        self.loop.run_until_complete(restore_model.restore())

        self.assertEqual(restore_model.to_dict()["state"], ModelState.READY)

    def test_should_restore_model_success_when_model_state_deleting(self):
        called_one = False
        called_two = False
        count = 0

        def delete_callback(delete_model):
            if count == 1:
                self.assertTrue(called_one)
            if count == 2:
                self.assertTrue(called_two)
            self.assertEqual(delete_model.namespace, self.config["namespace"])
            self.assertEqual(delete_model.name, self.config["name"])
            self.assertEqual(delete_model.version, self.config["version"])

        callbacks = {"on_delete_finish": delete_callback}
        model = Model(self.config, self.db, self.s3_agent, callbacks=callbacks)
        self.loop.run_until_complete(model.create())
        self.assertEqual(model.to_dict()["state"], ModelState.UNREADY)

        update_info = {"state": "success", "progress": "100"}
        model.update(update_info)
        self.assertEqual(model.to_dict()["state"], ModelState.READY)

        count += 1
        called_one = True
        self.loop.run_until_complete(model.delete())

        model_dict = model.to_dict()
        restore_model = Model(model_dict, self.db, self.s3_agent)

        count += 1
        called_two = True
        self.loop.run_until_complete(restore_model.restore())

    def test_should_model_transform_to_dict_success(self):
        model = Model(self.config, self.db, self.s3_agent)
        model_dict = model.to_dict()
        self.assertEqual(model_dict["namespace"], self.config["namespace"])
        self.assertEqual(model_dict["name"], self.config["name"])
        self.assertEqual(model_dict["runtime"], self.config["runtime"])
        self.assertEqual(model_dict["state"], ModelState.UNREADY)
        self.assertEqual(model_dict["version_info"]["version"],
                         self.config["version"])
        self.assertEqual(model_dict["version_info"]["description"],
                         self.config.get("description"))
        self.assertIsNotNone(model_dict["storage_info"])
        self.assertIsNotNone(model_dict["id"])


if __name__ == "__main__":
    unittest.main()
