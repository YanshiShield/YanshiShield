#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-few-public-methods, broad-except
"""Client main process.
"""
import uuid
from absl import logging
from grpclib.server import Stream

from neursafe_fl.proto.evaluate_service_grpc import EvaluateServiceBase
from neursafe_fl.proto.message_pb2 import Task, Response, Metadata
from neursafe_fl.proto.train_service_grpc import TrainServiceBase
from neursafe_fl.python.client.storage_manager import StorageManager
from neursafe_fl.python.client.task import TaskType
from neursafe_fl.python.client.task_manager import TaskManager, \
    is_finished_task_workspace_name
from neursafe_fl.python.client.validation import validate_task_info
from neursafe_fl.python.libs.secure.secure_aggregate.ssa_controller import \
    ssa_controller
from neursafe_fl.python.trans.grpc import GRPCServer
from neursafe_fl.python.trans.ssl_helper import SSLContext
from neursafe_fl.python.trans.grpc_call import unpackage_stream, \
    extract_metadata
from neursafe_fl.python.client.client_reporter import ClientReporter


# TODO proto interface need review and ajustment.
class TrainRpcService(TrainServiceBase):
    """The implement class of client grpc services. Receive grpc request from
    from server and run train task.
    """
    def __init__(self, **kwargs):
        self.__task_manager = kwargs['task_manager']
        self.__storage_manager = kwargs['storage_manager']

    async def Train(self, stream: Stream[Task, Response]):
        """Process train task.
        """
        try:
            self.__storage_manager.assert_storage_sufficient()

            task_info, files = await unpackage_stream(
                stream, validate_func=validate_task_info)
            grpc_metadata = extract_metadata(stream,
                                             keys=["module-id", "client_id"])

            logging.info('required train task info: %s', task_info)
            self.__task_manager.create(TaskType.train.name,
                                       task_info, files, grpc_metadata)
            await stream.send_message(Response(state='success'))
        except Exception as err:
            logging.exception(str(err))
            await stream.send_message(
                Response(state='failed', reason=str(err)))
            await stream.cancel()

    async def Stop(self, stream: Stream[Metadata, Response]):
        """Stop training."""
        try:
            task_metadata = await stream.recv_message()
            logging.info('required stop train task request: %s', task_metadata)
            self.__task_manager.stop(TaskType.train.name,
                                     task_metadata)
            await stream.send_message(Response(state='success'))
        except Exception as err:
            logging.exception(str(err))
            await stream.send_message(
                Response(state='failed', reason=str(err)))
            await stream.cancel()


class EvaluateRpcService(EvaluateServiceBase):
    """The implement class of client grpc services. Receive grpc request from
    from server and run evaluate task.
    """
    def __init__(self, **kwargs):
        self.__task_manager = kwargs['task_manager']
        self.__storage_manager = kwargs['storage_manager']

    async def Evaluate(self, stream: Stream[Task, Response]):
        """Process evaluate task.
        """
        try:
            self.__storage_manager.assert_storage_sufficient()

            task_info, files = await unpackage_stream(
                stream, validate_func=validate_task_info)
            grpc_metadata = extract_metadata(stream,
                                             keys=["module-id", "client_id"])

            logging.info('required evaluate task info: %s', task_info)
            self.__task_manager.create(TaskType.evaluate.name,
                                       task_info, files, grpc_metadata)
            await stream.send_message(Response(state='success'))
        except Exception as err:
            logging.exception(str(err))
            await stream.send_message(
                Response(state='failed', reason=str(err)))
            await stream.cancel()

    async def Stop(self, stream: Stream[Metadata, Response]):
        """Stop evaluating."""
        try:
            task_metadata = await stream.recv_message()
            logging.info('required stop evaluate task request: %s',
                         task_metadata)
            self.__task_manager.stop(TaskType.train.name,
                                     task_metadata)
            await stream.send_message(Response(state='success'))
        except Exception as err:
            logging.exception(str(err))
            await stream.send_message(
                Response(state='failed', reason=str(err)))
            await stream.cancel()


class Client:
    """Client, the edge computing in federated learning.
    """
    def __init__(self, config):
        self.__config = config
        self.__config["client_id"] = self.__gen_client_id()

        self.__task_manager = TaskManager(config)
        self.__reporter = ClientReporter(config, self.__task_manager)

        self.__storage_manager = StorageManager(
            monitor_path=config['workspace'],
            cleanable_file_matcher=is_finished_task_workspace_name,
            quota=config['storage_quota'])

    def __gen_client_id(self):
        client_uuid = str(uuid.uuid1())[10:]
        return "%s-%s" % (self.__config["platform"], client_uuid)

    async def start(self):
        """Start client, include storage manager and GRPC server.
        """
        self.__storage_manager.start()
        await self.__start_grpc_server([
            TrainRpcService(task_manager=self.__task_manager,
                            storage_manager=self.__storage_manager),
            EvaluateRpcService(task_manager=self.__task_manager,
                               storage_manager=self.__storage_manager),
            ssa_controller.grpc_service()])

    async def __start_grpc_server(self, services):
        ssl_context = SSLContext.instance(self.__config.get('ssl', None))
        grpc_server = GRPCServer(self.__config['host'],
                                 self.__config['port'],
                                 services,
                                 ssl_context)

        await grpc_server.start()
        logging.info('Start client success, listen port %s',
                     self.__config['port'])
        await self.__reporter.start()

        await grpc_server.wait_closed()
