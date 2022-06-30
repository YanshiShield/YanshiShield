#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""In this Model, We provide the interface to isolation resource by cgroup.
"""

from cgroupspy import trees
from absl import logging


_DEFAULT_CFS_PERIOD_US = 100000
_MB_2_BYTES = 1024 * 1024


class Cgroup():
    """Cgroup used to limit the use of cpu and memory in linux platform.

    Args:
        name: The name for this cgroup config, here is task id.
    """

    def __init__(self, name):
        tree = trees.Tree()
        self.__name = name
        self.__cpu_node = tree.get_node_by_path('/cpu/')
        self.__memory_node = tree.get_node_by_path('/memory/')

    def set_cpu_quota(self, pid, cpu_resource):
        """Set quota for CPU.

        Args:
            pid: The limited process id.
            cpu_resource: The CPU usage limit, unit core,
                example 0.2 core.
        """
        cpu_resource = cpu_resource * _DEFAULT_CFS_PERIOD_US
        logging.debug('set cpu limit %s', cpu_resource)
        cpu_cgroup = self.__cpu_node.create_cgroup(self.__name)
        cpu_cgroup.controller.cfs_quota_us = cpu_resource
        cpu_cgroup.controller.cfs_period_us = _DEFAULT_CFS_PERIOD_US
        cpu_cgroup.controller.tasks = pid

    def set_memory_quota(self, pid, memory_resource):
        """Set quota for memory.

        Args:
            pid: The limited process id.
            memory_resource: The memory usage limit, unit MB,
                example 1024 MB.
        """
        memory_resource = memory_resource * _MB_2_BYTES
        logging.info('set memory limit %s', memory_resource)
        memory_cgroup = self.__memory_node.create_cgroup(self.__name)
        memory_cgroup.controller.limit_in_bytes = memory_resource
        memory_cgroup.controller.tasks = pid

    def clear(self):
        """Clear the setting of cgroup.
        """
        self.__cpu_node.delete_cgroup(self.__name)
        self.__memory_node.delete_cgroup(self.__name)
