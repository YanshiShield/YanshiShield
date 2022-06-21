#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-few-public-methods, broad-except, too-many-arguments
# pylint:disable=broad-except, no-member
"""SSA: secret share aggregate.

algorithm reference:
Practical Secure Aggregation for Privacy-Preserving Machine Learning
https://dl.acm.org/doi/pdf/10.1145/3133956.3133982
"""
from absl import logging
from grpclib.server import Stream

from neursafe_fl.proto.message_pb2 import Response
from neursafe_fl.proto.secure_aggregate_grpc import SSAServiceBase
from neursafe_fl.proto.secure_aggregate_pb2 import SSAMessage


class SSAController:
    """The controller for SSA, used forward grpc message.
    """
    class SSAService(SSAServiceBase):
        """Partner grpc service.
        """
        def __init__(self, _ssa_controller):
            self.__ssa_controller = _ssa_controller

        async def call(self, stream: Stream[SSAMessage, Response]):
            """Process information call by the server/partner.
            """
            try:
                destination = stream.metadata["destination"]
                msg = await stream.recv_message()
                self.__ssa_controller.handle_msg(destination, msg)
                await stream.send_message(Response(state='success'))
            except Exception as err:
                logging.exception(str(err))
                await stream.send_message(
                    Response(state='failed', reason=str(err)))

    def __init__(self):
        self.__handlers = {}
        self.__ssa_service = self.SSAService(self)

    def grpc_service(self):
        """Get supported grpc services

        Return:
            ssa_service: Server used it to receive GRPC messages reported
                by the partner. Partner use it to receive GRPC messages
                sent by the server.
        """
        return self.__ssa_service

    def register_handler(self, handle, party, handler):
        """Register SSA server or SSA partner in handlers.

        Args:
            handle: Unique id for this encryption and decryption.
            party: the value is 'server' or partner id.
            handler: A object that implements SSABaseServer or SSABaseClient.
        """
        self.__handlers[(handle, party)] = handler

    def unregister_handler(self, handle, party):
        """
        Register SSA server or SSA partner in handlers

        Args:
            handle: Unique id for this encryption and decryption.
            party: the value is 'server' or partner id.
        """
        try:
            del self.__handlers[(handle, party)]
        except KeyError:
            logging.warning("%s already deleted.", handle)

    def handle_msg(self, destination, msg):
        """Message forwarding function.

        Args:
            destination: the value is 'server' or partner id.
            msg: messages reported by the partner, or send by the server.
        """
        self.__handlers[(msg.handle, destination)].handle_msg(msg)


# A singleton ssa controller.
ssa_controller = SSAController()
