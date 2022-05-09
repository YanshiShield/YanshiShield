#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-many-instance-attributes, invalid-name
"""Client Module.
"""
import time
import json
from absl import logging

from neursafe_fl.python.selector.clients.const import State, HeartBeat
from neursafe_fl.python.selector.utils import split, to_dict
from neursafe_fl.proto.message_pb2 import ClientState


class Client:
    """General client.

    General client defines basic general properties, methods, also includes
    some internal attributes for selector process.
    You can inherit from this class to customize client class, the custom client
    can add more properties or methods for more precise selection.

    Args:
        config: ClientInfo proto message.
    """

    def __init__(self, config):
        self.id = config.client.id
        self.type = config.client.type  # single or cluster
        self.address = config.address
        self.state = config.state
        self.max_parallelism = int(config.max_task_parallelism)
        self.cur_parallelism = int(config.cur_task_parallelism)
        self.os = config.os  # operate system
        self.runtime = split(config.runtime)
        self.label = split(config.client_label)

        self.resource = to_dict(config.client_resource)
        self.status = to_dict(config.client_status)
        self.data = to_dict(config.client_data)  # {"data_name": number}
        self.tasks = split(config.tasks)

        # internal attributes
        self.__heartbeat_interval = HeartBeat.get(self.type)
        self.__report_time = None  # last report time
        self.__expire_time = None  # last report time + heartbeat interval

        self.__history = []  # record the tasks have participated in

    def __str__(self):
        return "Type %s, ID %s" % (self.type, self.id)

    def assign_task(self, task_info):
        """Assign one task on this client.
        """
        # TODO should occupy the resources, to judge?
        self.cur_parallelism += 1
        self.tasks.append(task_info)
        if task_info not in self.__history:
            self.__history.append(task_info)

    def release_task(self, task_info):
        """The task is complete, release the client task.
        """
        if self.cur_parallelism > 0:
            self.cur_parallelism -= 1
        if task_info in self.tasks:
            self.tasks.remove(task_info)

    def update(self, config):
        """Update the client info with new report config.

        If some core states don't change, then can use the weight cache, no need
        to calculate in every query. And between each report, the weight can be
        reused.
        """
        self.os = config.os
        self.runtime = split(config.runtime)
        self.state = config.state
        self.address = config.address
        self.max_parallelism = int(config.max_task_parallelism)
        self.cur_parallelism = int(config.cur_task_parallelism)
        self.label = split(config.client_label)
        self.resource = to_dict(config.client_resource)
        self.status = to_dict(config.client_status)
        self.data = to_dict(config.client_data)
        self.tasks = split(config.tasks)

    def refresh_time(self):
        """Refresh report time and expire time.
        """
        self.__report_time = time.time()
        self.__expire_time = time.time() + self.__heartbeat_interval
        logging.info("Client expired time %s", self.__expire_time)

    def is_available(self):
        """Whether the client can be used.

        The client is not fully occupied by tasks and not expired, also state
        available.
        """
        if self.is_expired():
            logging.debug("Client %s is expired.", self)
            return False

        if (self.max_parallelism == -1
                or self.cur_parallelism < self.max_parallelism):
            if (self.state == ClientState.Value(State.Available)
                    or self.state == ClientState.Value(State.Idle)):
                return True
        logging.debug("Client %s state %s tasks %s not available.", self,
                      self.state, self.cur_parallelism)
        return False

    def match(self, conditions):
        """Check if the client match the condition.

        Normally, this method is used to determine whether the client has a
        certain attribute, such as os, runtime, label and so on.
        If the client has new attributes, you can inherit from this class and
        rewrite this match function.

        Args:
            conditions: proto (key, value) judge if client has the key attribute
                        with the same value.
        """
        for key in conditions:
            require_val = conditions[key]
            client_attr = getattr(self, str(key), None)
            if not client_attr:
                logging.debug("Client %s don't have %s", self, key)
                return False
            if not self.__check_value(key, client_attr, require_val):
                logging.debug("Client %s %s %s don't match require %s",
                              self, key, client_attr, require_val)
                return False
        logging.debug("Client %s match all the conditions.", self)
        return True

    def __check_value(self, attr_name, attr, require):
        if isinstance(attr, dict):
            return self._assert_valid(attr_name, attr, require)

        if isinstance(attr, list):
            return self._assert_in(attr, require)

        return self._assert_equal(attr, require)

    def _assert_valid(self, attr_name, attribute, require):
        if attr_name == "data":
            require = [key.strip() for key in require.split(",") if key.strip()]
            return self._assert_in(attribute.keys(), require)
        if attr_name == "resource":
            require = json.loads(require)
            for key in require:
                if key not in attribute or \
                        not self._assert_bigger(attribute[key], require[key]):
                    return False
        return True

    def _assert_equal(self, val1, val2):
        return val1 == val2

    def _assert_in(self, container, sub):
        if isinstance(sub, list):
            for key in sub:
                if key not in container:
                    return False
        else:
            if sub not in container:
                return False
        return True

    def _assert_bigger(self, val1, val2):
        return float(val1) > float(val2)

    def is_expired(self):
        """Judge whether the client is out of date.
        """
        if time.time() > self.__expire_time:
            return True
        return False

    def is_task_trained(self, task_info):
        """Judge if this client has already train the task.
        """
        if task_info in self.__history:
            return True
        return False

    def to_dict(self):
        """Transform the object to dict format.
        """
        return {
            "id": self.id,
            "type": self.type,
            "address": self.address,
            "state": self.state,
            "os": self.os,
            "max_task_parallelism": self.max_parallelism,
            "cur_task_parallelism": self.cur_parallelism,
            "runtime": self.runtime,
            "label": self.label,
            "resource": self.resource,
            "status": self.status,
            "data": self.data,
            "tasks": self.tasks
        }
