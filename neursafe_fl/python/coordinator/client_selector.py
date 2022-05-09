#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Client Select Module."""

import os
import random
from absl import logging

from neursafe_fl.python.coordinator.errors import DeviceNotEnoughError
from neursafe_fl.proto.message_pb2 import ClientRequirement, Metadata
from neursafe_fl.proto.select_service_grpc import SelectServiceStub
from neursafe_fl.python.trans.grpc_call import unary_call


class ClientSelector:
    """Select clients for federate learning.

    Client module mainly provide interface for coordinator to get clients
    for federated job. Clients can be config with IPs, or can be get from
    third-party service, such as Selector.
    """
    def __init__(self, config):
        self.__config = config
        self.__selector_address = os.getenv("SELECTOR_ADDRESS")
        self.__clients = []
        if config.get("clients"):
            clients = [client.strip() for client in config["clients"].split(",")
                       if client.strip()]
            self.__clients = clients  # clients from configuration

    async def select(self, demands):
        """Select interface for coordinator to select clients for training.
        for example, will construct ClientRequirements:
            {
                "task_info": metadata of task.
                "client_num": required client number.
                "redundancy": redundancy of the number of clients, value should
                              between 1 to 2. 1 means no redundancy. max
                              2 means double clients. Default 1.
                "random_client": True means random select clients from which
                                 meets the conditions, more applicable to
                                 fairness. False means select clients based on
                                 some strategy by sorted. Default is False.
                "conditions": the condition that the client must meet. such as
                              runtime, os etc.
            }

        Args:
            demands: basic requirement of clients.
        Returns:
            List of clients' service address.
        """
        if not self.__clients and not self.__selector_address:
            raise DeviceNotEnoughError("No clients to select for training.")

        if not self.__selector_address:  # only used when no selector server.
            return self.__select_from_config(demands)

        return await self.__select(demands)

    async def __select(self, demands):
        """Select clients from outside service, selector.
        """
        logging.info("Select training clients from selector.")
        requirements = self.__construct_message(demands)

        result = await unary_call(SelectServiceStub, "Select", requirements,
                                  self.__selector_address, None)

        if result.state == "success":
            logging.debug("Selector return clients %s", result.client_list)
            return self.__parse_ips(result.client_list)
        raise DeviceNotEnoughError(result.reason)

    def __construct_message(self, demands):
        task_info = Metadata(job_name=self.__config["job_name"])
        conditions = {"runtime": self.__config["runtime"]}
        if self.__config.get("datasets"):
            conditions["data"] = self.__config["datasets"]

        return ClientRequirement(task=task_info,
                                 number=demands["client_num"],
                                 random_client=self.__config.get(
                                     "random_client", False),
                                 untrained_first=self.__config.get(
                                     "untrained_first", False),
                                 redundancy=self.__config.get("redundancy", 1),
                                 conditions=conditions,
                                 clients=",".join(self.__clients))

    def __parse_ips(self, clients):
        """Find out the ip address from the client information.
        """
        client_ips = []
        for client in clients:
            client_ips.append(client.address)
        return client_ips

    def __select_from_config(self, demands):
        """Select clients from the clients in configuration.
        """
        logging.warning("No selector server, select training clients from"
                        "configuration.")
        if not demands:
            return self.__clients

        client_num = demands["client_num"]
        if len(self.__clients) < client_num:
            raise DeviceNotEnoughError("Left clients: %s not enough client for "
                                       "requirement: %s."
                                       % (len(self.__clients), client_num))
        # random pick client from all clients
        return random.sample(self.__clients, client_num)

    async def release(self):
        """Release the clients of current task.
        """
        if not self.__selector_address:
            return
        task_info = Metadata(job_name=self.__config["job_name"])
        await unary_call(SelectServiceStub, "Release", task_info,
                         self.__selector_address, None)
        logging.info("Release current round clients.")
