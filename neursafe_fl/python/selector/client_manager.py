#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-many-instance-attributes,assignment-from-none
"""Client Manager Module.
"""
import asyncio
import random
import math
from absl import logging

from neursafe_fl.python.selector.clients.client import Client
from neursafe_fl.python.selector.authenticator import Authenticator
from neursafe_fl.python.selector.clients.const import HeartBeat
from neursafe_fl.python.selector.evaluators.strategy import load_strategy
from neursafe_fl.python.selector.extender import load, filter_extender,\
    score_extender


class ClientManager:
    """Client manager class.

    Client manage all the Clients of selector, and implement the interface to
    add | delete | search | filter Clients.
    This module focus on management of Client, decoupling from Clients and
    selection strategies.
    The Clients will be organized as follows:
        {
            "type_1": {
                "id1": object(Client),
                "id2": object(Client),
            },
            "type_2": {
                "id1": object(Client)
            }
        }
    But the clients can support multiple ways of index, such as runtime, data.
    """

    def __init__(self, config):
        self.__config = config

        self.__clients = {}  # all the clients
        self.__indexes = {}  # construct multiple indexes for quick search.
        self.__client_number = 0  # current total number of clients
        self.__strategy = None
        self.__extenders = {}
        self.__monitor = None
        self.__auth = Authenticator(config.get("root_cert"))
        self.__is_auth = config.get("auth_client").lower() == "true"

        # the clients occupied by task, {"task_id": [occupied client list]}
        self.__occupied_clients = {}

    async def start(self):
        """Start the client manager.

        Do some initialization work here.
        """
        logging.info("Start initialize the client manager.")
        self.__load_strategy()
        self.__load_extenders()
        if not self.__is_auth:
            logging.info("Client authentication is off.")
        await self.__start_heartbeat_timer()

    async def stop(self):
        """Stop the client manager.

        Do some cleanup work here.
        """
        if self.__monitor:
            self.__monitor.cancel()

    def __load_strategy(self):
        """Load the selection strategy

        Strategy is used to score the client after the

        If set the 'optimal_select' to False in config, then we will random
        select the clients after filter.
        If not set the 'optimal_select', we will try to load the strategy
        according the config or using default strategy.
        """
        if self.__config["optimal_select"].lower() == "true":
            self.__strategy = load_strategy(self.__config.get("strategy"))
        else:
            self.__strategy = None
            logging.info("No strategy to load.")

    def __load_extenders(self):
        """Extender is used to extend the process client selection, it will be
        called after the strategy execution. extenders config example:
            {
                "filter": {
                }
                "score": {
                }
            }
        """
        support_extenders = ["filter", "score"]
        if not self.__config.get("extenders"):
            logging.info("Not find extenders in config.")
            return

        for method in support_extenders:
            config = self.__config["extenders"].get(method)
            if config:
                self.__extenders[method] = load(config)

    async def __start_heartbeat_timer(self):
        """Heartbeat timer is used to monitor whether the clients online.
        """
        self.__monitor = asyncio.ensure_future(self.__refresh_clients())

    async def __refresh_clients(self):
        """Refresh the clients.

        Delete the client which lost its heartbeat and time expired.
        """
        self.__remove_expired_clients()
        timeout = HeartBeat.min_time()
        await asyncio.sleep(timeout)
        self.__monitor = asyncio.ensure_future(self.__refresh_clients())

    def __remove_expired_clients(self):
        for client_type in self.__clients:
            for client_id in list(self.__clients[client_type].keys()):
                client = self.__clients[client_type][client_id]
                if client.is_expired():
                    logging.info("Remove expired client %s", client)
                    self.__remove_client(client)
        logging.info("Clean expired clients finish.")

    def register(self, auth_info):
        """Register client.

        Register this client to join in federate learning.
        """
        logging.info("Client %s register.", auth_info.client_id)
        if self.__is_auth:
            self.__auth.authenticate(auth_info)
        else:
            logging.warning("Authentication is off.")
        logging.info("Client %s register success.", auth_info.client_id)

    def report(self, client_info, metadata):
        """Client report client info.

        Report the client current info to client.
        """
        if self.__is_auth:
            self.__auth.verify(client_info, metadata["signature-bin"])

        logging.info("Receive client, info: %s", client_info)
        client_id, client_type = client_info.client.id, client_info.client.type
        if (self.__clients.get(client_type)
                and self.__clients[client_type].get(client_id)):
            client = self.__update_client(client_info)
        else:
            client = self.__add_client(client_info)

        client.refresh_time()  # set the client report time and expired time

    def __add_client(self, client_info):
        client = Client(client_info)
        if not self.__clients.get(client.type):
            self.__clients[client.type] = {}
        self.__clients[client.type][client.id] = client
        logging.info("Add client %s success", client)
        self.__add_index(client)  # add other indexes
        self.__client_number += 1
        return client

    def __add_index(self, client):
        address_index = "address"
        if address_index not in self.__indexes:
            self.__indexes[address_index] = {}
        self.__indexes[address_index][client.address] = client

    def __get_client_by_index(self, index, value):
        if index in self.__indexes:
            return self.__indexes[index].get(value)
        return None

    def __remove_index(self, client):
        address_index = "address"
        if self.__indexes.get(address_index):
            self.__indexes[address_index].pop(client.address)

    def __update_client(self, client_info):
        client = self.__clients[client_info.client.type][client_info.client.id]
        self.__remove_index(client)
        client.update(client_info)
        self.__add_index(client)
        logging.info("Update client %s success", client)
        return client

    def quit(self, client_info, metadata):
        """Client actively exit the federate learning.
        """
        if self.__is_auth:
            self.__auth.verify(client_info, metadata["signature-bin"])

        client = self.get(client_info.type, client_info.id)
        if client:
            self.__remove_client(client)
        else:
            logging.warning("Not found %s client %s",
                            client_info.type, client_info.id)

    def __remove_client(self, client):
        self.__clients[client.type].pop(client.id)
        if not self.__clients[client.type]:
            self.__clients.pop(client.type)
        self.__remove_index(client)

        if self.__client_number > 0:
            self.__client_number -= 1
        else:
            logging.warning("Client num abnormal is %s", self.__client_number)
            self.__check_clients_num()
            logging.warning("Check the clients real num is %s",
                            self.__client_number)

        logging.info("Remove client %s success.", client)

    def __check_clients_num(self):
        total_clients = 0
        for client_type in self.__clients:
            total_clients += len(self.__clients[client_type])
        self.__client_number = total_clients

    async def select_client(self, requirements):
        """Select client that match the requirements.

        This method is the core of selector. All clients will be selected
        according to the requirements. And the strategy will prioritize the
        client.

        Args:
            requirements: selection criteria to match the proper clients.
        Returns:
            list of suitable clients.
        """
        logging.info("Start select clients for require: %s", requirements)
        if requirements.clients:
            clients = self.__specify_clients(requirements.clients)
        else:
            clients = self.__filter_clients(requirements.conditions)

        if requirements.number > len(clients):
            raise Exception("Not enough client for require: %s" % requirements)

        redundant = self.__calc_redundancy(requirements)
        if requirements.number <= len(clients) <= redundant:
            # the client number is just satisfied, return all the clients.
            logging.info("Quantity satisfied, return all filtered clients.")
            self.__occupy_clients(requirements.task, clients)
            return clients

        if not self.__strategy or requirements.random_client is True:
            logging.info("Random select %s clients for require.", redundant)
            r_clients = random.sample(clients, redundant)
            self.__occupy_clients(requirements.task, r_clients)
            return r_clients

        # optimal selection, prioritize
        sorted_clients = self.__prioritize_clients(clients,
                                                   requirements.conditions)
        if requirements.untrained_first:
            sorted_clients = self.__try_sort_unused_clients(sorted_clients,
                                                            requirements.task)

        selected_clients = sorted_clients[0:redundant]
        logging.info("Optimal selection of clients success.")

        self.__occupy_clients(requirements.task, selected_clients)
        return selected_clients

    def __filter_clients(self, demands):
        qualified_clients = []
        for client_type in self.__clients:
            for client_id in self.__clients[client_type]:
                client = self.__clients[client_type][client_id]
                if client.is_available() and client.match(demands):
                    qualified_clients.append(client)

        qualified_clients = self.__run_filter_extender(qualified_clients)
        logging.info("Filter matched clients num: %s", len(qualified_clients))
        return qualified_clients

    def __run_filter_extender(self, clients):
        filter_func = self.__extenders.get("filter")
        if filter_func:
            format_clients = [client.to_dict() for client in clients]
            result = filter_extender(filter_func, format_clients)
            filtered = []
            for item in result:
                filtered.append(self.__clients[item["type"]][item["id"]])
            return filtered

        return clients

    def __calc_redundancy(self, requirements):
        redundancy = requirements.redundancy
        if not requirements.redundancy or requirements.redundancy < 1:
            redundancy = 1
        if requirements.redundancy > 2:
            redundancy = 2

        return math.ceil(redundancy * requirements.number)

    def __prioritize_clients(self, clients, conditions):
        """Prioritize clients.

        Args:
            clients: list. client objects to be sorted.
        Returns:
            list of client sorted by order.
        """
        # score the client
        sorted_clients = []
        for client in clients:
            score = self.__score_client(client, conditions)
            sorted_clients.append((score, client))
        logging.info("Score filtered clients success.")
        # sort the client base on score
        sorted_clients.sort(key=lambda x: x[0], reverse=True)
        logging.info("Prioritize clients success.")
        return [item[1] for item in sorted_clients]

    def __score_client(self, client, conditions):
        score = 0
        for _, evaluator in self.__strategy.items():
            score += evaluator.score(client, **conditions)
            score += self.__run_score_extender(client)
        logging.debug("Score of client %s is %s", client, score)
        return score

    def __run_score_extender(self, client):
        score_func = self.__extenders.get("score")
        if score_func:
            return score_extender(score_func, client.to_dict())
        return 0

    def __try_sort_unused_clients(self, sorted_clients, task_info):
        # select from untrained first, if not enough, the search from trained
        logging.info("Try to search untrained client first.")
        trained_clients = []
        untrained_clients = []
        for client in sorted_clients:
            if client.is_task_trained(task_info):
                trained_clients.append(client)
            else:
                untrained_clients.append(client)
        return untrained_clients + trained_clients

    def __specify_clients(self, clients_address):
        logging.info("Specify clients %s for selection.", clients_address)
        clients_address = clients_address.split(",")
        clients = []
        for address in clients_address:
            client = self.__get_client_by_index("address", address)
            if not client:
                logging.warning("Client %s not registered.", address)
            else:
                clients.append(client)
        return clients

    def __occupy_clients(self, task_info, clients):
        for client in clients:
            client.assign_task(task_info.job_name)

        self.__occupied_clients[task_info.job_name] = clients

    async def release_client(self, task_info):
        """Release the clients that being used in federated learning.

        Typically when each training round finished, should release the clients
        occupied by this task.

        Args:
            task_info: federate task's info that has occupied some clients.
        """
        task_id = task_info.job_name
        if task_id in self.__occupied_clients:
            clients = self.__occupied_clients[task_id]
            for client in clients:
                if self.exist(client.type, client.id):
                    client.release_task(task_id)
            del self.__occupied_clients[task_id]
        logging.info("Release task %s occupied clients.", task_id)

    def get(self, client_type, client_id):
        """Get client if exist, otherwise return None.
        """
        if self.exist(client_type, client_id):
            return self.__clients[client_type][client_id]
        return None

    def exist(self, client_type, client_id):
        """Whether the client is managed by selector.
        """
        if client_type in self.__clients:
            if client_id in self.__clients[client_type]:
                return True
        return False

    async def check_clients(self, requirements):
        """Check if the clients match the requirements.
        """
        logging.info("Check clients for require: %s", requirements)
        if requirements.number > self.__client_number:
            return "Not enough registered clients."

        if requirements.clients:
            clients = self.__specify_clients(requirements.clients)
        else:
            clients = self.__filter_clients(requirements.conditions)

        if requirements.number > len(clients):
            return "Not enough available clients currently for " \
                   "the training conditions."

        return None

    def __get_all_clients(self):
        """Traverse the clients and return all clients info.
        """
        clients = []
        for client_type in self.__clients:
            for client_id in self.__clients[client_type]:
                client = self.__clients[client_type][client_id]
                clients.append(client)
        return clients

    async def get_clients(self, requirements):
        """Return all the clients that match the conditions.
        """
        logging.info("Get clients for requirements %s.", requirements)
        if not requirements.conditions:
            return self.__get_all_clients()

        clients = self.__filter_clients(requirements.conditions)
        return clients

    def get_client_number(self):
        """Get current client number.
        """
        return self.__client_number

    def get_client_info(self):
        """Get client detail info.
        """
