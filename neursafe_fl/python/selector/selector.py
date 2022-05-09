#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Selector Module.
"""

from absl import logging

from neursafe_fl.python.trans.grpc import GRPCServer
from neursafe_fl.python.trans.ssl_helper import SSLContext
from neursafe_fl.python.selector.client_manager import ClientManager
from neursafe_fl.python.selector.grpc_services import ClientService, \
    SelectService


class Selector:
    """Selector component of federate learning system.
    """

    def __init__(self, config):
        self.__config = config
        self.__client_manager = None

    async def start(self):
        """Start selector service.
        """
        self.__client_manager = ClientManager(self.__config)
        await self.__client_manager.start()

        client_service = ClientService(self.__client_manager)
        select_service = SelectService(self.__client_manager)
        grpc_services = [client_service, select_service]

        await self.__start_grpc_server(grpc_services)

    async def stop(self):
        """Stop selector service.
        """

    async def __start_grpc_server(self, services):
        ssl_context = SSLContext.instance(self.__config.get("ssl", None))
        grpc_server = GRPCServer(self.__config["host"],
                                 self.__config["port"],
                                 services,
                                 ssl_context)

        await grpc_server.start()
        logging.info("Start grpc(s) service success on port %s",
                     self.__config["port"])

        await grpc_server.wait_closed()
