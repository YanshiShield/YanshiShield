#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=invalid-name
"""
Resource manager
"""
import collections
import threading
from absl import logging

import neursafe_fl.python.resource_manager.const as const
import neursafe_fl.python.resource_manager.errors as errors

from neursafe_fl.python.libs.db.db_factory import create_db
from neursafe_fl.python.resource_manager.plat_form.platform import \
    gen_platform, PlatFormType
from neursafe_fl.python.libs.db.errors import DataAlreadyExisting
from neursafe_fl.python.resource_manager.node import NodeState
import neursafe_fl.python.resource_manager.util as util


NodePriorityWeights = collections.namedtuple(
    "NodePriorityWeights", ["allocatable_worker_num", "left_gpu_num",
                            "left_cpu_num", "left_memory_num"])


class ResourceManager:
    """Resource Manager Class
    """

    def __init__(self):
        """
        nodes: {"node_id": Object(Node)...}
        tasks: {"task_id": List(resource_allocation_spec)}
        resource_allocation_spec: {"node_id": node_id,
                                   "resource": {"gpu": 2,
                                                "cpu": 2,
                                                "memory": 1024}}
        """
        self.__nodes = {}
        self.__tasks = {}

        self.__platform = gen_platform({"add": self.__add_node,
                                        "modify": self.__modify_node,
                                        "delete": self.__delete_node})
        self.__db_collection = None

        if const.PLATFORM in [PlatFormType.K8S]:
            self.__db_collection = create_db(const.DB_TYPE,
                                             db_server=const.DB_ADDRESS,
                                             db_name=const.DB_NAME,
                                             user=const.DB_USERNAME,
                                             pass_word=const.DB_PASSWORD).\
                get_collection(const.DB_COLLECTION_NAME)

    def start(self):
        """Start resource manager
        """
        self.__fetch_nodes()
        self.__watch_nodes()

        self.__restore_task()

    def __restore_task(self):
        if const.PLATFORM == PlatFormType.STANDALONE:
            logging.info("Platform is %s, no need to restore task.",
                         const.PLATFORM)
            return

        tasks = self.__db_collection.find_all()

        for task in tasks:
            self.__tasks[task["task_id"]] = task["resource_spec"]
            self.__occupy_resource(task["task_id"], task["resource_spec"])

        logging.info("Restore tasks successfully, tasks: %s", self.__tasks)

    def request(self, task_id, task_resource):
        """Request resource for task

        Args:
            task_id: task index
            task_resource: resource request config

        Raises:
            NoEnoughResource: no enough resource for resource request
        """
        logging.info("Resource request, task id: %s, resoure: %s", task_id,
                     task_resource)

        if task_id in self.__tasks:
            # fault tolerance process: task already exist, reallocate resource
            logging.info("Task: %s already exist, release first.", task_id)
            self.release(task_id)

        resource_allocation_spec = self.__allocate_resource(task_resource)
        logging.info("Resource allocation spec: task: %s, spec: %s.",
                     task_id,
                     resource_allocation_spec)

        self.__add_task(task_id, resource_allocation_spec)

        self.__occupy_resource(task_id, resource_allocation_spec)
        logging.info("Resource request, task id: %s successfully", task_id)

        return resource_allocation_spec

    def __occupy_resource(self, task_id, resource_allocation_spec):
        for resource_spec in resource_allocation_spec:
            if resource_spec["node_id"] in self.__nodes:
                self.__nodes[resource_spec["node_id"]].occupy_resource(
                    task_id, resource_spec["resource"])

    def __release_resource(self, task_id, resource_allocation_spec):
        for resource_spec in resource_allocation_spec:
            if resource_spec["node_id"] in self.__nodes:
                self.__nodes[resource_spec["node_id"]].release_resource(
                    task_id, resource_spec["resource"])

    def __allocate_resource(self, resource_request):
        # allocation policy: node least
        resource_allocation_spec = []
        filtered_nodes = self.__filter_nodes(resource_request)

        logging.info("Filtered nodes: %s",
                     [(weights, node.id) for weights, node in filtered_nodes])
        for node_priority_weights, node in filtered_nodes:
            result = self.__allocate_resource_in_node(
                node, node_priority_weights.allocatable_worker_num,
                resource_request["worker_resource"])
            resource_allocation_spec.extend(result)

        return resource_allocation_spec[0:resource_request["worker_num"]]

    def __allocate_resource_in_node(self, node, worker_num, worker_resource):
        resource_allocation_spec = []
        for _ in range(worker_num):
            resource_allocation_spec.append({"node_id": node.id,
                                             "resource": worker_resource})

        return resource_allocation_spec

    def __filter_nodes(self, resource_request):
        filtered_nodes = []
        total_allocatable_worker_num = 0

        for _, node in self.__nodes.items():
            if node.state == NodeState.NOTREADY:
                logging.warning("Node: %s not ready.", node.id)
                continue

            if node.cluster_label != const.CLUSTER_LABEL_VALUE:
                logging.warning(
                    "Node: %s cluster label: %s not belongs to cluster: %s",
                    node.id, node.cluster_label, const.CLUSTER_LABEL_VALUE)
                continue

            node_priority_weights = self.__calc_node_priority_weights(
                node, resource_request["worker_resource"])
            if node_priority_weights.allocatable_worker_num:
                filtered_nodes.append((node_priority_weights, node))
                total_allocatable_worker_num += node_priority_weights.\
                    allocatable_worker_num

            if total_allocatable_worker_num >= resource_request["worker_num"]:
                sorted(filtered_nodes, key=lambda element: element[0],
                       reverse=True)
                return filtered_nodes

        raise errors.NoEnoughResource(
            "No enough resource for request: %s" % resource_request)

    def __calc_node_priority_weights(self, node, worker_resource):
        """
        Calculate node priority weights(allocatable_worker_num, left_gpu_num,
        left_cpu_num, left_memory_num), weight priority is:
        allocatable_worker_num > left_gpu_num > left_cpu_num > left_memory_num,
        higher weight value means high priority
        """
        allocatable_worker_num = self.__calc_allocatable_worker_num(
            node, worker_resource)
        left_gpu_num = node.gpu.volume - node.gpu.\
            allocated - allocatable_worker_num * worker_resource.get("gpu", 0)
        left_cpu_num = node.cpu.volume - node.cpu.\
            allocated - allocatable_worker_num * worker_resource.get("cpu", 0)
        left_memory_num = node.memory.volume - node.\
            memory.allocated - allocatable_worker_num * worker_resource.\
            get("memory", 0)

        return NodePriorityWeights(allocatable_worker_num, left_gpu_num,
                                   left_cpu_num, left_memory_num)

    def __calc_allocatable_worker_num(self, node, worker_resource):
        cpu_limit_worker_num = self.__calc_limit_worker_num(
            node.cpu.volume - node.cpu.allocated, worker_resource.get(
                "cpu", 0.0))

        gpu_limit_worker_num = self.__calc_limit_worker_num(
            node.gpu.volume - node.gpu.allocated, worker_resource.get("gpu", 0))

        memory_limit_worker_num = self.__calc_limit_worker_num(
            node.memory.volume - node.memory.allocated,
            worker_resource.get("memory", 0))

        return min(cpu_limit_worker_num, gpu_limit_worker_num,
                   memory_limit_worker_num)

    def __calc_limit_worker_num(self, allocatable_num, request_num):
        if request_num == 0:
            return float("inf")

        return int(allocatable_num / request_num)

    def release(self, task_id):
        """Release task resource

        Args:
            task_id: task index, which task will be released resource
        """
        logging.info("Release task: %s resource", task_id)
        self.__release_resource(task_id, self.__tasks.get(task_id, []))
        self.__del_task(task_id)
        logging.info("Release task: %s resource successfully.", task_id)

    def __add_task(self, task_id, resource_allocation_spec):
        task_spec = {"task_id": task_id,
                     "resource_spec": resource_allocation_spec}
        self.__persist(task_spec)
        self.__tasks[task_id] = resource_allocation_spec

    @util.db_operation_retry
    def __persist(self, task_spec):
        if self.__db_collection:
            try:
                self.__db_collection.insert(task_spec)
            except DataAlreadyExisting:
                self.__db_collection.update({"task_id": task_spec["task_id"]},
                                            task_spec)

    def __del_task(self, task_id):
        if self.__db_collection:
            self.__db_collection.delete({"task_id": task_id})

        if task_id in self.__tasks:
            del self.__tasks[task_id]

    def __fetch_nodes(self):
        nodes = self.__platform.fetch_nodes()

        for node in nodes:
            self.__nodes[node.id] = node

        logging.info("Fetch nodes: %s successfully.", list(self.__nodes.keys()))

    def __watch_nodes(self):
        logging.info("Begin watch nodes.")
        sub_thread = threading.Thread(target=self.__platform.watch_nodes)
        sub_thread.setDaemon(True)
        sub_thread.start()

    def __modify_node(self, node_id, new_node):
        if node_id != new_node.id:
            logging.info("Node id: %s not same with new node id, no need to "
                         "modify", node_id, new_node.id)
            return

        if node_id in self.__nodes:
            self.__nodes[node_id].update(new_node)
        else:
            self.__nodes[node_id] = new_node

    def __delete_node(self, node_id):
        logging.info("Delete node: %s", node_id)
        if node_id in self.__nodes:
            del self.__nodes[node_id]

    def __add_node(self, node):
        logging.info("Add node: %s", node.info)
        if node.id in self.__nodes:
            self.__nodes[node.id].update(node)
        else:
            self.__nodes[node.id] = node
