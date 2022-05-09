#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=missing-function-docstring, protected-access, no-member, invalid-name
"""UnitTest of SSA Partner.
"""
import asyncio
from collections import OrderedDict
import unittest

import numpy as np

from neursafe_fl.python.libs.secure.secure_aggregate.ssa_client import SSAClient
from neursafe_fl.python.libs.secure.secure_aggregate.common import ProtocolStage,\
    PseudorandomGenerator


class TestSSAClient(unittest.TestCase):
    """Test class of SSA Partner.
    """
    def setUp(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        handle = 'jobname-1'
        server_address = '9.8.7.6:110'
        ssl_path = None
        partner_id = 'my_id'
        wait_mask_generated_timeout = 1
        wait_alive_clients_timeout = 1
        threshold = 2
        max_num = 2
        self.__client = SSAClient(
            handle, server_address, ssl_path, partner_id,
            threshold, max_num, False, None,
            wait_mask_generated_timeout, wait_alive_clients_timeout)
        self.__other_client_dh_keys = {}

    def test_should_success_encrypt_int(self):
        prg = PseudorandomGenerator(1234)
        self.__client._b = 1234
        self.__client._s_uv_s = [("my_ia", PseudorandomGenerator(1234)),
                                 ("my_ie", PseudorandomGenerator(1234))]
        self.__client._SSAClient__stage = ProtocolStage.CiphertextAggregate
        result = self.__client.encrypt(1)

        self.assertEqual(result, 1 + prg.next_number())

    def test_should_success_encrypt_np_array(self):
        prg = PseudorandomGenerator(1234)
        self.__client._b = 1234
        self.__client._s_uv_s = [("my_ia", PseudorandomGenerator(1234)),
                                 ("my_ie", PseudorandomGenerator(1234))]
        self.__client._SSAClient__stage = ProtocolStage.CiphertextAggregate

        np_array = np.ones((1, 2, 3), dtype=np.int16)
        new_array = self.__client.encrypt(np_array)
        self.assertTrue(
            self.__equal(new_array, np.full_like(new_array, 1 + prg.next_number())))

    def test_should_success_encrypt_list(self):
        prg = PseudorandomGenerator(1234)
        self.__client._b = 1234
        self.__client._s_uv_s = [("my_ia", PseudorandomGenerator(1234)),
                                 ("my_ie", PseudorandomGenerator(1234))]
        self.__client._SSAClient__stage = ProtocolStage.CiphertextAggregate

        np_array_list = [np.ones((2, 2, 3), dtype=np.int16),
                         np.full((3, 1, 3), 2)]
        new_array_list = self.__client.encrypt(np_array_list)

        self.assertTrue(self.__equal(new_array_list[0],
                                     np.full((2, 2, 3), 1 + prg.next_number())))
        self.assertTrue(self.__equal(new_array_list[1],
                                     np.full_like(new_array_list[1], 2 + prg.next_number())))

    def test_should_success_encrypt_dict(self):
        prg = PseudorandomGenerator(1234)
        self.__client._b = 1234
        self.__client._s_uv_s = [("my_ia", PseudorandomGenerator(1234)),
                                 ("my_ie", PseudorandomGenerator(1234))]
        self.__client._SSAClient__stage = ProtocolStage.CiphertextAggregate

        np_array = np.ones((1, 2, 3), dtype=np.int16)
        ordered_dict = OrderedDict()
        ordered_dict['int'] = 1
        ordered_dict['float'] = 1.1
        ordered_dict['array'] = np_array
        new_dict = self.__client.encrypt(ordered_dict)
        self.assertEqual(new_dict['int'], 1 + prg.next_number())
        self.assertEqual(new_dict['float'], 1.1 + prg.next_number())
        self.assertTrue(self.__equal(new_dict['array'],
                                     np.full_like(new_dict['array'], 1 + prg.next_number())))

    def __equal(self, array1, array2):
        for index, value in enumerate(array1):
            result = abs(value - array2[index]) < 0.000001
            if not result.all():
                return False
        return True


class TestSSAClientWithUseSameMask(unittest.TestCase):
    """Test class of SSA Partner.
    """
    def setUp(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        handle = 'jobname-1'
        server_address = '9.8.7.6:110'
        ssl_path = None
        partner_id = 'my_id'
        wait_mask_generated_timeout = 1
        wait_alive_clients_timeout = 1
        threshold = 2
        max_num = 2
        self.__client = SSAClient(
            handle, server_address, ssl_path, partner_id,
            threshold, max_num, True, None,
            wait_mask_generated_timeout, wait_alive_clients_timeout)
        self.__other_client_dh_keys = {}

    def test_should_success_encrypt_list(self):
        prg = PseudorandomGenerator(1234)
        mask = prg.next_number()
        self.__client._b = 1234
        self.__client._s_uv_s = [("my_ia", PseudorandomGenerator(1234)),
                                 ("my_ie", PseudorandomGenerator(1234))]
        self.__client._SSAClient__stage = ProtocolStage.CiphertextAggregate

        np_array_list = [np.ones((2, 2, 3), dtype=np.int16),
                         np.full((3, 1, 3), 2)]
        new_array_list = self.__client.encrypt(np_array_list)

        self.assertTrue(self.__equal(new_array_list[0],
                                     np.full((2, 2, 3), 1 + mask)))
        self.assertTrue(self.__equal(new_array_list[1],
                                     np.full_like(new_array_list[1], 2 + mask)))

    def test_should_success_encrypt_dict(self):
        prg = PseudorandomGenerator(1234)
        mask = prg.next_number()
        self.__client._b = 1234
        self.__client._s_uv_s = [("my_ia", PseudorandomGenerator(1234)),
                                 ("my_ie", PseudorandomGenerator(1234))]
        self.__client._SSAClient__stage = ProtocolStage.CiphertextAggregate

        np_array = np.ones((1, 2, 3), dtype=np.int16)
        ordered_dict = OrderedDict()
        ordered_dict['int'] = 1
        ordered_dict['float'] = 1.1
        ordered_dict['array'] = np_array
        new_dict = self.__client.encrypt(ordered_dict)
        self.assertEqual(new_dict['int'], 1 + mask)
        self.assertEqual(new_dict['float'], 1.1 + mask)
        self.assertTrue(self.__equal(new_dict['array'],
                                     np.full_like(new_dict['array'], 1 + mask)))

    def __equal(self, array1, array2):
        for index, value in enumerate(array1):
            result = abs(value - array2[index]) < 0.000001
            if not result.all():
                return False
        return True


if __name__ == "__main__":
    unittest.main()
