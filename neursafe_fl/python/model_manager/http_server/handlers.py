#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=abstract-method, broad-except, attribute-defined-outside-init
"""HTTP handlers.
"""
import json
from absl import logging

from tornado.web import RequestHandler
from tornado import gen

from neursafe_fl.python.model_manager.utils.errors import (NotExist,
                                                           RequestError,
                                                           ServiceException)


class BaseRequestHandler(RequestHandler):
    """Base http handler.
    """
    def write_result(self, code, result):
        """http response.

        Args:
            code: http code.
            result: http response body
        """
        self.set_status(code)
        self.write(json.dumps(result))

    def write_success(self, code):
        """Success http response
        """
        result = {"state": "SUCCEEDED"}

        self.write_result(code, result)

    def write_failed(self, code, error_reason):
        """Failed http response

        Args:
            code: http code.
            error_reason: error message.
        """
        result = {"state": "FAILED",
                  "reason": error_reason}

        self.write_result(code, result)


class ModelsHandler(BaseRequestHandler):
    """Handle models request in one namespace.
    """

    URL = r'/api/v1/namespaces/(.*)/models'

    def initialize(self, model_manager):
        """Initialize with model manager as processor.
        """
        self.__model_manager = model_manager

    @gen.coroutine
    def post(self, namespace):
        """Create model interface.
        """
        try:
            model_config = json.loads(self.request.body)
            model = yield self.__model_manager.create_model(namespace,
                                                            model_config)
            self.write_result(201, model)
        except (KeyError, TypeError, ValueError) as err:
            logging.info(str(err))
            self.write_failed(400, str(err))
        except NotExist as err:
            logging.info(str(err))
            self.write_failed(404, str(err))
        except ServiceException as err:
            logging.error(str(err))
            self.write_failed(500, str(err))
        except Exception as err:
            logging.exception(str(err))
            self.write_failed(503, str(err))

    def get(self, namespace):
        """Get models interface.
        """
        try:
            models = self.__model_manager.get_models(namespace)
            self.write_result(200, {"models": models})
        except NotExist as err:
            logging.info(str(err))
            self.write_failed(404, str(err))
        except Exception as err:
            logging.exception(str(err))
            self.write_failed(503, str(err))


class ModelHandler(BaseRequestHandler):
    """Handle model request, required operation on specified model.
    """

    URL = r'/api/v1/namespaces/(.*)/models/([\w|\-]{0,100})'

    def initialize(self, model_manager):
        """Initialize with model manager as processor.
        """
        self.__model_manager = model_manager

    def get(self, namespace, model_name):
        """Get one model interface.
        """
        try:
            version = self.get_argument("version", None)
            model = self.__model_manager.get_model(namespace, model_name,
                                                   version)
            self.write_result(200, {"models": model})
        except NotExist as err:
            logging.info(str(err))
            self.write_failed(404, str(err))
        except Exception as err:
            logging.exception(str(err))
            self.write_failed(500, str(err))

    def put(self, namespace, model_name):
        """Update one model interface.
        """
        try:
            version = self.get_argument("version", None)
            update_info = json.loads(self.request.body)
            model = self.__model_manager.update_model(update_info, namespace,
                                                      model_name, version)
            self.write_result(200, model)
        except NotExist as err:
            logging.info(str(err))
            self.write_failed(404, str(err))
        except ServiceException as err:
            logging.error(str(err))
            self.write_failed(500, str(err))
        except Exception as err:
            logging.exception(str(err))
            self.write_failed(503, str(err))

    @gen.coroutine
    def delete(self, namespace, model_name):
        """Delete one model interface.
        """
        try:
            version = self.get_argument("version", None)
            yield self.__model_manager.delete_model(namespace, model_name,
                                                    version)
            self.write_success(200)
        except NotExist as err:
            logging.info(str(err))
            self.write_failed(404, str(err))
        except RequestError as err:
            logging.info(str(err))
            self.write_failed(400, str(err))
        except ServiceException as err:
            logging.error(str(err))
            self.write_failed(500, str(err))
        except Exception as err:
            logging.exception(str(err))
            self.write_failed(503, str(err))


class ModelIDHandler(BaseRequestHandler):
    """Handle model request base on the unique id of model.
    """
    URL = r'/api/v1/models'

    def initialize(self, model_manager):
        """Initialize with model manager as processor.
        """
        self.__model_manager = model_manager

    def get(self):
        """Get model through its id.
        """
        try:
            model_id = self.get_argument("model_id", None)
            model = self.__model_manager.get_model_by_id(model_id)
            self.write_result(200, model)
        except NotExist as err:
            logging.info(str(err))
            self.write_failed(404, str(err))
        except Exception as err:
            logging.exception(str(err))
            self.write_failed(503, str(err))

    def put(self):
        """Update model by id.
        """
        try:
            model_id = self.get_argument("model_id", None)
            update_info = json.loads(self.request.body)
            model = self.__model_manager.update_model(update_info,
                                                      model_id=model_id)
            self.write_result(200, model)
        except NotExist as err:
            logging.info(str(err))
            self.write_failed(404, str(err))
        except ServiceException as err:
            logging.error(str(err))
            self.write_failed(500, str(err))
        except Exception as err:
            logging.exception(str(err))
            self.write_failed(503, str(err))

    @gen.coroutine
    def delete(self):
        """Delete model through its id.
        """
        try:
            model_id = self.get_argument("model_id", None)
            yield self.__model_manager.delete_model_by_id(model_id)
            self.write_success(200)
        except NotExist as err:
            logging.info(str(err))
            self.write_failed(404, str(err))
        except RequestError as err:
            logging.info(str(err))
            self.write_failed(400, str(err))
        except ServiceException as err:
            logging.error(str(err))
            self.write_failed(500, str(err))
        except Exception as err:
            logging.exception(str(err))
            self.write_failed(503, str(err))


class HealthHandler(BaseRequestHandler):
    """Health handler to check server ok.
    """
    URL = r'/api/v1/health'

    def get(self):
        """Health OK interface.
        """
        try:
            self.write_result(200, "OK")
        except Exception as error:
            logging.exception(str(error))
            self.write_error(503)
