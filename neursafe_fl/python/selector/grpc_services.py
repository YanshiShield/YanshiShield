#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=invalid-name, broad-except, unused-variable, unused-argument
# pylint:disable=no-member
"""gRPC services of selector.
"""
from absl import logging
from grpclib.server import Stream

from neursafe_fl.proto.client_service_grpc import ClientServiceBase
from neursafe_fl.proto.select_service_grpc import SelectServiceBase
from neursafe_fl.proto.message_pb2 import (ClientRequirement, ClientList,
                                           Client, Metadata, Response,
                                           ClientInfo, ClientRegister)


class SelectService(SelectServiceBase):
    """Selector interface for other server component.

    Service provides interface to select client for federate training, or some
    statistics of current clients.
    """

    def __init__(self, client_manager):
        self.__client_manager = client_manager

    async def Select(self, stream: Stream[ClientRequirement, ClientList]):
        requirements = await stream.recv_message()
        try:
            clients = await self.__client_manager.select_client(requirements)
            clients_proto = _to_proto(clients)
            await stream.send_message(clients_proto)
        except Exception as err:
            logging.exception(str(err))
            await stream.send_message(
                ClientList(state='failed', reason=str(err)))

    async def Release(self, stream: Stream[Metadata, Response]):
        task_info = await stream.recv_message()
        try:
            await self.__client_manager.release_client(task_info)
            await stream.send_message(Response(state="success"))
        except Exception as err:
            logging.exception(str(err))
            await stream.send_message(
                Response(state='failed', reason=str(err)))

    async def CheckClientsResource(self, stream: Stream[ClientRequirement,
                                                        Response]):
        requirements = await stream.recv_message()
        try:
            result = await self.__client_manager.check_clients(requirements)
            if not result:
                await stream.send_message(Response(state="success"))
            else:
                await stream.send_message(Response(state='failed',
                                                   reason=result))
        except Exception as err:
            logging.exception(str(err))
            await stream.send_message(
                Response(state='failed', reason="System Internal Error."))

    async def GetClients(self, stream: Stream[ClientRequirement, ClientList]):
        requirements = await stream.recv_message()
        try:
            clients = await self.__client_manager.get_clients(requirements)
            clients_proto = _to_proto(clients)
            await stream.send_message(clients_proto)
        except Exception as err:
            logging.exception(str(err))
            await stream.send_message(
                ClientList(state='failed', reason=str(err)))


class ClientService(ClientServiceBase):
    """Client interface for client(client).

    Service provides interface for client to join or quit the federate
    learning
    """

    def __init__(self, client_manager):
        self.__client_manager = client_manager

    async def Register(self, stream: Stream[ClientRegister, Response]):
        register_info = await stream.recv_message()
        try:
            self.__client_manager.register(register_info)
            await stream.send_message(Response(state="success"))
        except Exception as err:
            logging.exception(str(err))
            await stream.send_message(
                Response(state='failed', reason=str(err)))

    async def Report(self, stream: Stream[ClientInfo, Response]):
        metadata = stream.metadata
        client_info = await stream.recv_message()
        try:
            _check_parameters(client_info)
            self.__client_manager.report(client_info, metadata)
            await stream.send_message(Response(state="success"))
        except Exception as err:
            logging.exception(str(err))
            await stream.send_message(
                Response(state='failed', reason=str(err)))

    async def Quit(self, stream: Stream[Client, Response]):
        metadata = stream.metadata
        client_info = await stream.recv_message()
        try:
            self.__client_manager.quit(client_info, metadata)
            await stream.send_message(Response(state="success"))
        except Exception as err:
            logging.exception(str(err))
            await stream.send_message(
                Response(state='failed', reason=str(err)))


def _check_parameters(client_info):
    """Check  whether the reported client information is legal.
    """


def _to_proto(clients):
    """Transform the client from python object to proto buffer.

    Args:
        clients: list of client object
    Returns:
        proto ClientList
    """
    proto_clients = []
    for client in clients:
        tmp = ClientInfo(client=Client(id=client.id, type=client.type),
                         address=client.address, os=client.os,
                         tasks=",".join(client.tasks),
                         client_label=",".join(client.label),
                         runtime=",".join(client.runtime),
                         cur_task_parallelism=client.cur_parallelism,
                         client_data=client.data)
        proto_clients.append(tmp)
    result = ClientList(state="success", num=len(clients))
    result.client_list.extend(proto_clients)
    return result
