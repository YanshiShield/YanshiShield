#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=broad-except
"""K8s platform
"""
import re
import math
from absl import logging

from neursafe_fl.python.resource_manager.plat_form.base import Platform
from neursafe_fl.python.resource_manager.node import NodeState, Node
from neursafe_fl.python.libs.cloud.kube_client import KubeClient, EventType
from neursafe_fl.python.libs.cloud.errors import GetNodesError, WatchNodesError
from neursafe_fl.python.resource_manager.plat_form.errors import PlatformError
import neursafe_fl.python.resource_manager.util as util
import neursafe_fl.python.resource_manager.const as const


def _get_ready_status(conditions):
    """get node ready status
    """
    for condition in conditions:
        if condition.type == "Ready":
            return _get_boolean(condition.status)

    return False


def _get_boolean(p_str):
    """
    convert string to bool
    """
    if p_str.lower() == "true":
        return True

    return False


def _get_node_id(node_info):
    return node_info.metadata.name


def _get_cpu_volume(node_info):
    try:
        cpu_num_info = node_info.status.allocatable["cpu"]

        if cpu_num_info == '':
            return 0

        if isinstance(cpu_num_info, int):
            return cpu_num_info

        if cpu_num_info[-1] == 'm':
            return math.floor(int(cpu_num_info[:-1]) / 1000)

        return int(cpu_num_info)
    except Exception as error:
        logging.warning(str(error))
        return 0


def _get_node_state(node_info):
    conditions = node_info.status.conditions

    if _get_ready_status(conditions):
        return NodeState.READY

    return NodeState.NOTREADY


def _get_memory_volume(node_info):
    unit_convert_map = {'K': 1000 ** -1,
                        'KI': 1024 ** -1,
                        'M': 1,
                        'MI': 1,
                        'G': 1000,
                        'GI': 1024,
                        'T': 1000 ** 2,
                        'TI': 1024 ** 2,
                        'P': 1000 ** 3,
                        'PI': 1024 ** 3,
                        'E': 1000 ** 4,
                        'EI': 1024 ** 4}

    try:
        memory_info = node_info.status.allocatable["memory"]

        if isinstance(memory_info, int):
            return memory_info

        unit = re.search(r"[A-Z]+", memory_info.upper()).group()
        value = int(re.search(r"\d+", memory_info).group())

        return value * unit_convert_map[unit]
    except Exception as err:
        logging.warning(str(err))
        return 0


def _get_gpu_volume(node_info):
    try:
        if const.GPU_RS_KEY not in node_info.status.allocatable:
            return 0

        gpu_info = node_info.status.allocatable[const.GPU_RS_KEY]

        if isinstance(gpu_info, int):
            return gpu_info

        return int(gpu_info)
    except Exception as error:
        logging.warning(str(error))
        return 0


def _get_cluster_label(node_info):
    return node_info.metadata.labels.get(const.CLUSTER_LABEL_KEY)


class Kubernetes(Platform):
    """Kubernetes platform class
    """

    def __init__(self, event_callbacks):
        super().__init__(event_callbacks)
        self.__kube_client = KubeClient()

    @util.platform_operation_retry
    def fetch_nodes(self):
        """Return k8s nodes

        Returns:
            nodes: a list of Node object.
        """
        try:
            nodes = []
            k8s_nodes = self.__kube_client.get_nodes()
            logging.debug("Get k8s nodes: %s", k8s_nodes)
        except GetNodesError as error:
            logging.error(str(error))
            raise PlatformError() from error

        for k8s_node in k8s_nodes:
            node = Node(_get_node_id(k8s_node),
                        _get_node_state(k8s_node),
                        cpu_volume=_get_cpu_volume(k8s_node),
                        gpu_volume=_get_gpu_volume(k8s_node),
                        memory_volume=_get_memory_volume(k8s_node),
                        cluster_label=_get_cluster_label(k8s_node))
            nodes.append(node)

        return nodes

    def __watch_node_callbacks(self):
        def add_node(k8s_node):
            node = Node(_get_node_id(k8s_node),
                        _get_node_state(k8s_node),
                        cpu_volume=_get_cpu_volume(k8s_node),
                        gpu_volume=_get_gpu_volume(k8s_node),
                        memory_volume=_get_memory_volume(k8s_node),
                        cluster_label=_get_cluster_label(k8s_node))
            self._event_callbacks["add"](node)

        def modify_node(k8s_node):
            node = Node(_get_node_id(k8s_node),
                        _get_node_state(k8s_node),
                        cpu_volume=_get_cpu_volume(k8s_node),
                        gpu_volume=_get_gpu_volume(k8s_node),
                        memory_volume=_get_memory_volume(k8s_node),
                        cluster_label=_get_cluster_label(k8s_node))
            self._event_callbacks["modify"](node.id, node)

        def delete_node(k8s_node):
            self._event_callbacks["delete"](_get_node_id(k8s_node))

        return {EventType.ADD: add_node,
                EventType.DELETE: delete_node,
                EventType.MODIFY: modify_node}

    def watch_nodes(self):
        """Watch nodes
        """
        try:
            self.__kube_client.watch_nodes(self.__watch_node_callbacks())
        except WatchNodesError as error:
            logging.error(str(error))
            raise PlatformError() from error
