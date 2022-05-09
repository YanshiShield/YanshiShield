#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Grpc server.
"""

from grpclib.server import Server
from grpclib.utils import graceful_exit


class GRPCServer:
    """Server for GRPC.

    Args:
        host: The listen host ip.
        port: The listen port.
        services: The grpc server will load these services.
        ssl_certificate: When used grpcs, set a SSLContext.
    """
    def __init__(self, host, port, services, ssl_certificate=None):
        self.__host = host
        self.__port = port
        self.__services = services
        self.__ssl_certificate = ssl_certificate
        self.__server = Server(self.__services)

    async def start(self):
        """Start GRPC server.
        """
        with graceful_exit([self.__server]):
            await self.__server.start(self.__host, self.__port,
                                      ssl=self.__ssl_certificate)

    async def wait_closed(self):
        """Wait for server closed
        """
        await self.__server.wait_closed()

    def close(self):
        """Direct close the server."""
        self.__server.close()
