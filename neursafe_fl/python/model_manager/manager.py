#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-many-arguments
"""Model Manager.
"""
from absl import logging

from tornado.web import gen

from neursafe_fl.python.model_manager.validations import validate_config
from neursafe_fl.python.model_manager.model import Model
from neursafe_fl.python.model_manager.storage.storage_agent import StorageAgent
from neursafe_fl.python.model_manager.utils.db import DBAdaptor
import neursafe_fl.python.model_manager.utils.errors as error


class ModelManager:
    """Model manager manage all the models.

    Model manager is also the model store for federated learning. Typically
    manage the metadata of model, and the real storage path in the backend.

    The model will be organized by follows:
        {
            "namespace": {
                "model_name": {
                    "version": object(model)
                }
            }
        }
    """

    def __init__(self):
        self.__models = {}
        self.__id_index = {}
        self.__db = DBAdaptor()
        self.__storage_agent = StorageAgent()
        self.__callbacks = {"on_delete_finish": self.on_delete_finish}
        self.__versions = {}

    @gen.coroutine
    def start(self):
        """Start model manager.

        Do some initialization work here.
        """
        logging.info("Initialize model manager.")
        yield self.__restore_models()

    @gen.coroutine
    def __restore_models(self):
        """Restore all the models from database.
        """
        model_configs = self.__db.read_all()
        for config in model_configs:
            model = Model(config, self.__db, self.__storage_agent,
                          callbacks=self.__callbacks)
            yield model.restore()
            logging.info("Restore model %s from db.", model)
            self.__add_model(model.namespace, model)

    def get_model_by_id(self, model_id):
        """Every model has a unique id.

        User can query the model by just one id.
        """
        self.__assert_model_id_exist(model_id)
        return self.__id_index[model_id].to_dict()

    def get_model(self, namespace, name, version=None):
        """Get specified model in namespace.

        If version is not specified, then will return all the versions of model.
        Otherwise will return the specified version of model.

        Args:
            namespace: namespace the model belong.
            name: model name
            version: specified version name of this model
        Returns:
            the list of model object with dict format.
        """
        self.__assert_model_exist(namespace, name)

        models = []
        if version:  # get specified version of model
            self.__assert_version_exist(namespace, name, version)
            version_model = self.__models[namespace][name][version]
            models.append(version_model.to_dict())

        else:  # get all versions of model
            version_models = self.__models[namespace][name]
            for model in version_models.values():
                models.append(model.to_dict())

        return {name: models}

    def get_models(self, namespace):
        """Get all the exist models name in the namespace.

        Args:
            namespace: the namespace looking for.
        Returns:
            the list of model name in this namespace.
        """
        self.__assert_namespace_exist(namespace)

        models = {}
        for model_name in self.__models[namespace]:
            model_versions = self.__models[namespace][model_name]
            models[model_name] = []
            for _, model in model_versions.items():
                models[model_name].append(model.to_dict())

        return models

    def __assert_model_id_exist(self, model_id):
        if model_id not in self.__id_index:
            raise error.ModelIDNotExist("Not found model id %s." % model_id)

    def __assert_namespace_exist(self, namespace):
        if namespace not in self.__models:
            raise error.ModelNotExist("Namespace %s has no models." % namespace)

    def __assert_model_exist(self, namespace, name):
        if not self.__is_model_exist(namespace, name):
            raise error.ModelNotExist("Model %s-%s not exist."
                                      % (namespace, name))

    def __assert_version_exist(self, namespace, name, version):
        if not self.__is_model_exist(namespace, name, version):
            raise error.ModelNotExist("Model %s-%s-%s not exist."
                                      % (namespace, name, version))

    def __assert_version_not_exist(self, namespace, name, version):
        if not version:
            return
        if self.__is_model_exist(namespace, name, version):
            raise error.ModelAlreadyExist("Model %s-%s-%s already exist."
                                          % (namespace, name, version))

    def __is_model_exist(self, namespace, name, version=None):
        """Check if the model exist.
        """
        try:
            if version:
                _ = self.__models[namespace][name][version]
            else:
                _ = self.__models[namespace][name]
            return True
        except KeyError:
            return False

    @gen.coroutine
    def create_model(self, namespace, config):
        """Create a new model to model store.
        """
        self.__assert_version_not_exist(namespace, config["name"],
                                        config.get("version"))

        config["namespace"] = namespace
        config["version"] = self.__gen_model_version(config)
        validate_config(config)

        model = Model(config, self.__db, self.__storage_agent,
                      callbacks=self.__callbacks)
        yield model.create()
        self.__add_model(namespace, model)
        raise gen.Return(model.to_dict())

    def __gen_model_version(self, config):
        """Generate a new version if user not set one.

        Typically will increase 1 with the version number every time, and will
        guaranteed not to be duplicated with existing versions.
        """
        if config.get("version"):
            return config["version"]
        namespace, name = config["namespace"], config["name"]
        model_key = "%s-%s" % (namespace, name)
        version_id = self.__versions.get(model_key, 0)

        version = "V%s" % version_id
        while self.__is_model_exist(namespace, name, version):
            version_id += 1
            version = "V%s" % version_id

        self.__versions[model_key] = version_id + 1
        return version

    def __add_model(self, namespace, model):
        if namespace not in self.__models:
            self.__models[namespace] = {
                model.name: {model.version: model}
            }
        else:
            models = self.__models[namespace]
            if model.name not in models:
                models[model.name] = {model.version: model}
            else:
                models[model.name][model.version] = model

        self.__id_index[model.id] = model  # add id index

    def update_model(self, update_info, namespace=None, name=None,
                     version=None, model_id=None):
        """Update model state or information.
        """
        if model_id in self.__id_index:
            model = self.__id_index[model_id]
        else:
            self.__assert_version_exist(namespace, name, version)
            model = self.__models[namespace][name][version]

        model.update(update_info)
        return model.to_dict()

    @gen.coroutine
    def delete_model(self, namespace, name, version=None):
        """delete model in the storage.

        If version not specified, then will delete all versions of this model.
        """
        self.__assert_model_exist(namespace, name)

        if not version:  # delete all the versions of model
            logging.warning("Delete model %s-%s all versions.",
                            namespace, name)
            versions = list(self.__models[namespace][name].keys())
            for version_name in versions:
                model = self.__models[namespace][name][version_name]
                yield model.delete()

        else:  # delete specified versions of model
            self.__assert_version_exist(namespace, name, version)
            model = self.__models[namespace][name][version]
            yield model.delete()

    def on_delete_finish(self, model):
        """Callback when model delete finished.
        """
        logging.info("Delete model %s in manager.", model)
        self.__remove_model(model.namespace, model)

    @gen.coroutine
    def delete_model_by_id(self, model_id):
        """Delete model through id.
        """
        self.__assert_model_id_exist(model_id)
        model = self.__id_index[model_id]
        yield model.delete()

    def __remove_model(self, namespace, model):
        self.__models[namespace][model.name].pop(model.version)
        if not self.__models[namespace][model.name]:
            self.__models[namespace].pop(model.name)
        if not self.__models[namespace]:
            self.__models.pop(namespace)

        self.__id_index.pop(model.id)
