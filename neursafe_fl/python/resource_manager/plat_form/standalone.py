#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
Stand alone platform(local host)
"""

import socket
from absl import logging

import pynvml
import psutil

from neursafe_fl.python.resource_manager.node import Node, NodeState
from neursafe_fl.python.resource_manager.plat_form.base import Platform


class Standalone(Platform):
    """Stand alone platform class
    """
    def fetch_nodes(self):
        """Return nodes

        Returns:
            nodes: a list of nodes, in this scene, nodes list only have one node
                (local host node)
        """
        gpu_volume = self.__get_gpu_num()
        cpu_volume = psutil.cpu_count()
        memory_volume = int(psutil.virtual_memory().total / (1024 * 1024))

        hostname = socket.gethostname()

        node = Node(hostname,
                    NodeState.READY,
                    cpu_volume=cpu_volume,
                    gpu_volume=gpu_volume,
                    memory_volume=memory_volume)

        return [node]

    def __get_gpu_num(self):
        try:
            pynvml.nvmlInit()
            return pynvml.nvmlDeviceGetCount()
        except pynvml.NVMLError as error:
            logging.warning(str(error))
            logging.warning('GPU environment initialization failed, '
                            'GPU is unavailable')
            return 0

    def watch_nodes(self):
        """Watch nodes

        Standalone scene no need to watch node
        """
        logging.info("Standalone scene no need to watch node.")
