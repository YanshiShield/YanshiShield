#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-few-public-methods
"""Node Definition
"""
from absl import logging

from neursafe_fl.python.resource_manager.resource import GPU, CPU, Memory


class NodeState:
    """Node state definition
    """
    READY = "READY"
    NOTREADY = "NOTREADY"


class Node:
    """Node class definition
    """

    def __init__(self, node_id, state, **kwargs):
        self.__id = node_id

        self.__gpu = GPU(kwargs.get("gpu_volume", 0))
        self.__cpu = CPU(float(kwargs.get("cpu_volume", 0.0)))
        self.__memory = Memory(kwargs.get("memory_volume", 0))
        self.__cluster_label = kwargs.get("cluster_label")

        self.__state = state
        """
        tasks: {"task_id": {"cpu": 1,
                            "gpu": 1,
                            "memory": 1024},
                ...}
        """
        self.__tasks = {}

    def occupy_resource(self, task_id, resources):
        """Occupy node resource

        Args:
             task_id: task index
             resources: resources to be occupied
        """
        self.__add_task_resource(task_id, resources)
        self.__occupy_resource(resources)
        logging.info("Occupy resource successfully: node: %s, task: %s, "
                     "resources: %s", self.__id, task_id, resources)

    def __occupy_resource(self, resources):
        self.__cpu.allocated += resources.get("cpu", 0)
        self.__gpu.allocated += resources.get("gpu", 0)
        self.__memory.allocated += resources.get("memory", 0)

    def __add_task_resource(self, task_id, resources):
        if task_id in self.__tasks:
            self.__tasks[task_id]["cpu"] += resources.get("cpu", 0)
            self.__tasks[task_id]["gpu"] += resources.get("gpu", 0)
            self.__tasks[task_id]["memory"] += resources.get("memory", 0)
        else:
            self.__tasks[task_id] = {}
            self.__tasks[task_id]["cpu"] = resources.get("cpu", 0)
            self.__tasks[task_id]["gpu"] = resources.get("gpu", 0)
            self.__tasks[task_id]["memory"] = resources.get("memory", 0)

    def release_resource(self, task_id, resources):
        """Release node resource

        Args:
            task_id: task index
            resources: resources to be released
        """
        if task_id in self.__tasks:
            self.__del_task_resource(task_id, resources)
            self.__release_resource(resources)
        logging.info("Release resource successfully: node: %s, task: %s, "
                     "resources: %s", self.__id, task_id, resources)

    def __del_task_resource(self, task_id, resources):
        self.__tasks[task_id]["cpu"] += resources.get("cpu", 0)
        self.__tasks[task_id]["gpu"] += resources.get("gpu", 0)
        self.__tasks[task_id]["memory"] += resources.get("memory", 0)

        if self.__tasks[task_id]["cpu"] == 0 and \
                self.__tasks[task_id]["gpu"] == 0 and \
                self.__tasks[task_id]["memory"] == 0:
            del self.__tasks[task_id]

    def __release_resource(self, resources):
        self.__cpu.allocated -= resources.get("cpu", 0)
        self.__gpu.allocated -= resources.get("gpu", 0)
        self.__memory.allocated -= resources.get("memory", 0)

    def update(self, new_node):
        """Update node

        Args:
            new_node: new node object
        """
        if self.__update_needed(new_node):
            logging.info("Update node: %s, origin info: %s, new info: %s",
                         self.__id, self.info, new_node.info)
            self.__cpu.volume = new_node.cpu.volume
            self.__gpu.volume = new_node.gpu.volume
            self.__memory.volume = new_node.memory.volume

            self.__state = new_node.state
            self.__cluster_label = new_node.cluster_label

            for task_id, task_resource in self.__tasks.items():
                self.occupy_resource(task_id, task_resource)

    def __update_needed(self, new_node):
        if new_node.cpu.volume != self.__cpu.volume:
            return True

        if new_node.gpu.volume != self.__gpu.volume:
            return True

        if new_node.memory.volume != self.__memory.volume:
            return True

        if new_node.state != self.__state:
            return True

        if new_node.cluster_label != self.__cluster_label:
            return True

        return False

    @property
    def state(self):
        """Return node state

        Returns:
            state: node state
        """
        return self.__state

    @property
    def cpu(self):
        """Return cpu resource object

        Returns:
            cpu: cpu resource object
        """
        return self.__cpu

    @property
    def gpu(self):
        """Return gpu resource object

        Returns:
            gpu: gpu resource object
        """
        return self.__gpu

    @property
    def memory(self):
        """Return memory resource object

        Returns:
            memory: memory resource object
        """
        return self.__memory

    @property
    def id(self):  # pylint:disable=invalid-name
        """Return node id

        Returns:
            id: node id(host name)
        """
        return self.__id

    @property
    def cluster_label(self):
        """Return node belongs to which cluster"""
        return self.__cluster_label

    @property
    def info(self):
        """Return node info

        Returns:
            node info: a dict object about node
        """
        node_info = {
            "id": self.__id,
            "state": self.__state,
            "cluster": self.__cluster_label,
            "cpu": {"volume": self.__cpu.volume,
                    "allocated": self.__cpu.allocated},
            "gpu": {"volume": self.__gpu.volume,
                    "allocated": self.__gpu.allocated},
            "memory": {"volume": self.__memory.volume,
                       "allocated": self.__memory.allocated},
            "tasks": self.__tasks
        }

        return node_info
