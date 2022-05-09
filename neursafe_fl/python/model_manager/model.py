#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-many-instance-attributes, too-few-public-methods
"""Model
"""
import os
import time
from collections import namedtuple
from absl import logging
from tornado.ioloop import IOLoop
from tornado.web import gen

from neursafe_fl.python.model_manager.utils.tools import current_time
from neursafe_fl.python.model_manager.utils.const import MODEL_STORE, \
    MOUNT_PATH, HEARTBEAT_TIMEOUT, RETRY_TIMES, RETRY_TIMEOUT
from neursafe_fl.python.model_manager.utils.errors import ModelStateError


class ModelState:
    """Model state
    """
    UNREADY = "unready"
    READY = "ready"
    ERROR = "error"
    DELETING = "deleting"


VersionInfo = namedtuple("VersionInfo", "version, time, description")


class Model:
    """Model class.

    The metadata of federate model.
    """

    def __init__(self, config, db, storage_agent, **kwargs):
        self.__namespace = config["namespace"]
        self.__name = config["name"]
        self.__runtime = config["runtime"]

        self.__model_path = config.get("model_path")
        self.__file_name = config.get("file_name")
        self.__db = db
        self.__storage_agent = storage_agent
        self.__callbacks = kwargs.get("callbacks", {})
        self.__heartbeat_timer = None
        self.__retry_count = 0

        self.__version_info = self.__gen_version_info(config)
        self.__storage_info = self.__gen_storage_info()
        self.__state = config.get("state", ModelState.UNREADY)
        self.__error_msg = config.get("error_msg")
        self.__progress = config.get("progress", 0)
        self.__id = self.__gen_model_id()

    def __str__(self):
        return "%s-%s-%s" % (self.namespace, self.name,
                             self.__version_info.version)

    def __gen_version_info(self, config):
        if config.get("version_info"):
            return VersionInfo(**config["version_info"])

        return VersionInfo(version=config["version"], time=current_time(),
                           description=config.get("description"))

    def __gen_storage_info(self):
        """The storage of model in cloud.

        when user upload model, should upload to 'model_store' with
        path '/namespace/model/version'.
        """
        model_path = "/%s/%s/%s" % (self.__namespace, self.__name,
                                    self.__version_info.version)
        if self.__model_path:
            file_name = os.path.basename(self.__model_path)
            model_path = os.path.join(model_path, file_name)
        elif self.__file_name:
            model_path = os.path.join(model_path, self.__file_name)

        storage = (MODEL_STORE, model_path)
        return storage

    def __gen_model_id(self):
        """The model id is unique within all namespaces.
        """
        return "%s-%s-%s" % (self.__namespace, self.__name,
                             self.__version_info.version)

    @gen.coroutine
    def create(self):
        """Create model.

        There are two ways to upload model to the model store.
            1. From user local file.
            2. From cloud storage path file.
        """
        if self.__model_path:  # from the cloud storage path
            logging.info("Start copy model from cloud.")
            yield self.__copy_model()
        else:  # from local file, waiting for uploading
            logging.info("Start wait for model upload.")
            self.__start_heartbeat_timer()

        self.__save_in_db()

    @gen.coroutine
    def __copy_model(self):
        cloud_source = self.__model_path.split(":")
        src = {"namespace": cloud_source[0],
               "path": cloud_source[1]}
        target = {"namespace": self.__storage_info[0],
                  "path": self.__storage_info[1]}
        yield self.__storage_agent.copy(src, target, self.__copy_callback)

    def __copy_callback(self, response):
        logging.info("Copy finished with %s", response)
        if response.state == "success":
            self.__state = ModelState.READY
        else:
            self.__error_msg = response.message
            self.__state = ModelState.ERROR
            if response.code != 404:
                self.__retry_copy()

        self.__save_in_db()

    def __retry_copy(self):
        logging.info("Retry copy after %s seconds.", RETRY_TIMEOUT)
        self.__retry_count += 1
        if self.__retry_count < RETRY_TIMES:
            IOLoop.instance().add_timeout(RETRY_TIMEOUT, self.__copy_model)
        else:
            logging.warning("Retry max %s, create failed.", RETRY_TIMES)

    def __start_heartbeat_timer(self):
        timeout_time = time.time() + HEARTBEAT_TIMEOUT
        self.__heartbeat_timer = IOLoop.instance().add_timeout(
            timeout_time, self.__heartbeat_timeout)

    def update(self, update_info):
        """Update model info.

        Update model information:
        1. update the progress if create model.
        2. update the entire model parameters.
        """
        logging.info("Model %s update with %s", self, update_info)
        if update_info.get("progress") or update_info.get("state"):
            self.__upload_heartbeat(update_info)
        else:
            raise NotImplementedError("Model update not implement currently.")

    def __upload_heartbeat(self, heartbeat_info):
        self.__stop_heartbeat_timer()
        if heartbeat_info.get("state") == "success":
            self.__state = ModelState.READY
        elif heartbeat_info.get("state") == "failed":
            self.__state = ModelState.ERROR
        else:
            self.__progress = heartbeat_info.get("progress")
            self.__start_heartbeat_timer()

        self.__save_in_db()

    def __stop_heartbeat_timer(self):
        if self.__heartbeat_timer:
            self.__heartbeat_timer.cancel()

    def __heartbeat_timeout(self):
        logging.info("Model %s upload timeout.", self)
        self.__state = ModelState.ERROR
        self.__heartbeat_timer = None
        self.__save_in_db()

    @gen.coroutine
    def delete(self):
        """Delete model, delete from the cloud.
        """
        logging.info("Delete model %s.", self)
        if self.__state in [ModelState.DELETING, ModelState.UNREADY]:
            raise ModelStateError("Model %s state %s, cannot delete now." %
                                  (self, self.__state))
        self.__state = ModelState.DELETING
        self.__save_in_db()
        yield self.__do_delete()

    @gen.coroutine
    def __do_delete(self):
        target = {"namespace": self.__storage_info[0],
                  "path": self.__storage_info[1]}
        yield self.__storage_agent.delete(target, self.__delete_callback)

    def __delete_callback(self, response):
        logging.info("Model %s delete finished with %s.", self, response)
        if response.state == "success" or response.code == 404:
            self.__delete_in_db()
            if self.__callbacks.get("on_delete_finish"):
                self.__callbacks["on_delete_finish"](self)
        else:
            IOLoop.instance().add_timeout(RETRY_TIMEOUT, self.__do_delete)

    def __save_in_db(self):
        if self.__db.exist(self):
            self.__db.update(self)
        else:
            self.__db.save(self)

    def __delete_in_db(self):
        self.__db.delete(self)

    @gen.coroutine
    def restore(self):
        """Store model state and info when restart.
        """
        if self.__state == ModelState.UNREADY:
            yield self.create()

        if self.__state == ModelState.DELETING:
            yield self.__do_delete()

    def to_dict(self):
        """Transform the model object into json format.
        """
        return {
            "namespace": self.__namespace,
            "name": self.__name,
            "runtime": self.__runtime,
            "id": self.__id,
            "state": self.__state,
            "version_info": self.__version_info._asdict(),
            "storage_info": self.__storage_info,
            "model_path": self.__model_path,
            "file_name": self.__file_name,
            "error_msg": self.__error_msg
        }

    def is_exist(self):
        """Check if the model exist in path.

        Typically the model storage path is organized as:
            /mount_point/model_bucket/namespace/model/version
        """
        model_store, path = self.__storage_info[0], self.__storage_info[1]
        absolute_path = os.path.join(MOUNT_PATH, "%s%s" % (model_store, path))
        if os.path.exists(absolute_path):
            return True
        return False

    @property
    def version(self):
        """The version name of model.
        """
        return self.__version_info.version

    @property
    def namespace(self):
        """The namespace of model.
        """
        return self.__namespace

    @property
    def name(self):
        """The name of model.
        """
        return self.__name

    @property
    def id(self):  # pylint:disable=invalid-name
        """The unique id of model.
        """
        return self.__id
