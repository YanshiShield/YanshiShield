#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-few-public-methods,broad-except
"""Define server gRPC services."""
from grpclib.server import Stream
from absl import logging

from neursafe_fl.python.trans.grpc_call import unpackage_stream
from neursafe_fl.proto.message_pb2 import TaskResult, Response, Metadata
from neursafe_fl.proto.reply_service_grpc import TrainReplyServiceBase
from neursafe_fl.proto.reply_service_grpc import EvaluateReplyServiceBase
from neursafe_fl.proto.job_stop_service_grpc import JobStopServiceBase


class Message:
    """Message type from client."""
    TRAIN = "report_train"
    EVALUATE = "report_evaluate"
    STOP = "stop"


class TrainReplyService(TrainReplyServiceBase):
    """Receive train result service."""

    def __init__(self, msg_mux):
        self.__msg_mux = msg_mux

    async def TrainReply(self, stream: Stream[TaskResult, Response]):
        try:
            # parse params and files from stream
            params, files = await unpackage_stream(stream)
            await self.__msg_mux(Message.TRAIN, (params, files))
            await stream.send_message(Response(state='success'))
        except ValueError as err:
            await stream.send_message(
                Response(state='failed', reason=str(err)))
            await stream.cancel()
        except Exception as err:
            # maybe CancelledError, no need send failed to client
            logging.exception(str(err))


class EvaluateReplyService(EvaluateReplyServiceBase):
    """Receive evaluate result service."""

    def __init__(self, msg_mux):
        self.__msg_mux = msg_mux

    async def EvaluateReply(self, stream: Stream[TaskResult, Response]):
        try:
            params, files = await unpackage_stream(stream)
            await self.__msg_mux(Message.EVALUATE, (params, files))
            await stream.send_message(Response(state='success'))
        except ValueError as err:
            await stream.send_message(
                Response(state='failed', reason=str(err)))
            await stream.cancel()
        except Exception as err:
            logging.exception(str(err))


class StopService(JobStopServiceBase):
    """Receive stop service.

    Stop command, force to stop current federate learning job.
    """

    def __init__(self, msg_mux):
        self.__msg_mux = msg_mux

    async def Stop(self, stream: Stream[Metadata, Response]):
        """Receive stop command."""
        try:
            await self.__msg_mux(Message.STOP, None)
            await stream.send_message(Response(state='success'))
        except ValueError as err:
            await stream.send_message(
                Response(state='failed', reason=str(err)))
            await stream.cancel()
        except Exception as err:
            logging.exception(str(err))
