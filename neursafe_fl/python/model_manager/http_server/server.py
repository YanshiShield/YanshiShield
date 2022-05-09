#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-few-public-methods
"""Http server.
"""
from absl import logging
from tornado.ioloop import IOLoop
import tornado.web

from neursafe_fl.python.model_manager.utils.const import HTTP_PORT
import neursafe_fl.python.model_manager.http_server.handlers as handlers


class Server:
    """Server of http
    """
    def __init__(self, model_manager):
        self.__model_manager = model_manager

    def start(self):
        """Start the http server
        """
        app = tornado.web.Application([
            (handlers.ModelsHandler.URL,
             handlers.ModelsHandler, {"model_manager": self.__model_manager}),
            (handlers.ModelHandler.URL,
             handlers.ModelHandler, {"model_manager": self.__model_manager}),
            (handlers.ModelIDHandler.URL,
             handlers.ModelIDHandler, {"model_manager": self.__model_manager}),
            (handlers.HealthHandler.URL, handlers.HealthHandler)
        ])
        app.listen(HTTP_PORT)
        logging.info("Http server start at port: %s.", HTTP_PORT)
        IOLoop.current().start()
