#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=missing-function-docstring,protected-access,invalid-name
"""
Test for Resource manager
"""
import unittest

from neursafe_fl.python.resource_manager.node import Node, NodeState
from neursafe_fl.python.resource_manager.rm import ResourceManager


class RMTest(unittest.TestCase):
    """test rm object"""

    def setUp(self) -> None:
        self.__rm = ResourceManager()

    def test_allocate_rs_successfully(self):
        node = Node("xxx",
                    NodeState.READY,
                    cpu_volume=16,
                    gpu_volume=0,
                    memory_volume=10000)
        self.__rm._ResourceManager__nodes = {node.id: node}

        rs_spec = self.__rm.request("task", {
            "worker_num": 1,
            "worker_resource": {"cpu": 1.0,
                                "gpu": 0,
                                "memory": 1000}})

        self.assertEqual(rs_spec, [{"node_id": "xxx",
                                    "resource": {"cpu": 1.0,
                                                 "gpu": 0,
                                                 "memory": 1000}}])


if __name__ == '__main__':
    unittest.main()
