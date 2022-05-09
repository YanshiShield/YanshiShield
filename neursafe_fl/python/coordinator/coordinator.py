#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-few-public-methods
"""Coordinator Module."""
from absl import logging

from neursafe_fl.python.libs.secure.secure_aggregate.ssa_controller import \
    ssa_controller
from neursafe_fl.python.coordinator.grpc_services import EvaluateReplyService
from neursafe_fl.python.coordinator.grpc_services import StopService
from neursafe_fl.python.coordinator.grpc_services import TrainReplyService
from neursafe_fl.python.coordinator.trainer import Trainer
from neursafe_fl.python.trans.grpc import GRPCServer
from neursafe_fl.python.trans.grpc_pool import GRPCPool
from neursafe_fl.python.trans.ssl_helper import SSLContext


class Coordinator:
    """Federated learning entry point class.

    Coordinator start the main process and service of federated learning.

    Args:
        config: the detailed configuration parameters of federated job.
    """
    def __init__(self, config):
        self.__config = config
        self.__trainer = None

    async def start(self):
        """Start Coordinator process for federate learning.

        First all services, including gRpc, http .etc will be created here.
        Then construct execution objects according to the job type, such as
        Trainer, Evaluator and so on. Finally start the process and services.
        """
        logging.info("Federate learning config: %s", self.__config)

        self.__trainer = Trainer(self.__config)

        # all the grpc services
        train_svc = TrainReplyService(self.__trainer.msg_mux)
        eval_svc = EvaluateReplyService(self.__trainer.msg_mux)
        stop_svc = StopService(self.__trainer.msg_mux)
        grpc_services = [train_svc, eval_svc, stop_svc]

        if ("secure_algorithm" in self.__config
                and self.__config["secure_algorithm"]["type"].lower() == 'ssa'):
            grpc_services.append(ssa_controller.grpc_service())

        grpc_server = await self.__start_grpc_server(grpc_services)

        await self.__trainer.start()

        GRPCPool.instance().close_all()
        grpc_server.close()

    async def __start_grpc_server(self, services):
        ssl_context = SSLContext.instance(self.__config.get('ssl', None))
        server = GRPCServer(self.__config['host'], self.__config['port'],
                            services, ssl_certificate=ssl_context)

        await server.start()
        logging.info("Start grpc service at port %s", self.__config['port'])

        return server
