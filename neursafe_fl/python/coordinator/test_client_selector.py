#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=missing-function-docstring
"""Client Selector UnitTest."""
import unittest
import asyncio

from neursafe_fl.python.coordinator.client_selector import ClientSelector
from neursafe_fl.python.coordinator.errors import DeviceNotEnoughError

CONFIG = {
    "clients": "0.0.0.1:77981, 0.0.0.1:77982, 0.0.0.1:77983"
}


class TestClientSelector(unittest.TestCase):
    """Test class."""

    def setUp(self) -> None:
        self.client_selector = ClientSelector(CONFIG)

    def test_should_select_clients_success_when_match_policy(self):
        policy = {"client_num": 1, "redundancy": 1}
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(self.client_selector.select(policy))
        self.assertEqual(len(result), 1)

        policy = {"client_num": 2, "redundancy": 1}
        result = loop.run_until_complete(self.client_selector.select(policy))
        self.assertEqual(len(result), 2)

    def test_should_select_clients_success_when_available_clients_enough(self):
        policy = {"client_num": 3, "redundancy": 1}
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(self.client_selector.select(policy))
        self.assertEqual(len(result), 3)

    def test_should_select_clients_failed_when_available_clients_not_enough(self):
        policy = {"client_num": 4, "redundancy": 1}
        with self.assertRaises(DeviceNotEnoughError):
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.client_selector.select(policy))

    def test_should_selector_init_failed_when_config_format_error(self):
        error_config = ["1", "2"]
        with self.assertRaises(Exception):
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.client_selector.select(error_config))

    def test_should_return_all_clients_when_policy_is_none(self):
        loop = asyncio.get_event_loop()
        clients = loop.run_until_complete(self.client_selector.select(
            demands=None))
        self.assertEqual(len(clients), 3)


if __name__ == "__main__":
    unittest.main()
