#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=missing-function-docstring, protected-access, no-member, invalid-name
"""UnitTest of SSA server.
"""
import asyncio
from collections import OrderedDict
import unittest
import numpy as np

from neursafe_fl.python.libs.secure.secure_aggregate.common import ProtocolStage, \
    PseudorandomGenerator, PLAINTEXT_MULTIPLE
from neursafe_fl.python.libs.secure.secure_aggregate.ssa_server import SSAServer

from neursafe_fl.proto.secure_aggregate_pb2 import EncryptedShares, EncryptedShare, \
    SecretShares, SecretShare
from neursafe_fl.python.utils.log import set_log

set_log()


class TestSSAServer(unittest.TestCase):
    """Test class of SSA server.
    """
    def setUp(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        handle = "jobname-1"
        min_num = 3
        max_num = 3
        wait_use_decrypt_timeout = 10
        ssl_path = None
        self.__server = SSAServer(handle, min_num, max_num,
                                  wait_use_decrypt_timeout, ssl_path)

    def test_should_success_accumulate_and_decrypt_with_int(self):
        prg = PseudorandomGenerator(1234)
        self.__server._b_masks = [PseudorandomGenerator(1234)]
        self.__server._s_uv_masks = [("1", "2", PseudorandomGenerator(1234)),
                                     ("2", "1", PseudorandomGenerator(1234))]
        self.__server._SSAServer__stage = ProtocolStage.CiphertextAggregate
        self.__server.ciphertext_accumulate(2, '1')
        result = self.__server.ciphertext_accumulate(4, '2')
        self.assertEqual(result, 6)
        self.assertEqual(self.__server._SSAServer__rpt_masked_result_clients,
                         ['1', '2'])

        result = self.__server._SSAServer__do_decrypt()
        self.assertEqual(result, (6 - prg.next_value()) / PLAINTEXT_MULTIPLE)

    def test_should_success_accumulate_and_decrypt_with_array(self):
        prg = PseudorandomGenerator(1234)
        self.__server._b_masks = [PseudorandomGenerator(1234)]
        self.__server._s_uv_masks = [("1", "2", PseudorandomGenerator(1234)),
                                     ("2", "1", PseudorandomGenerator(1234))]
        self.__server._SSAServer__stage = ProtocolStage.CiphertextAggregate

        self.__server.ciphertext_accumulate(np.full((1, 2, 3), 2),
                                            '1')
        result = self.__server.ciphertext_accumulate(np.full((1, 2, 3), 3),
                                                     '2')

        self.assertTrue(self.__equal(result, np.full((1, 2, 3), 5)))
        self.assertEqual(self.__server._SSAServer__rpt_masked_result_clients,
                         ['1', '2'])

        result = self.__server._SSAServer__do_decrypt()
        self.assertTrue(
            self.__equal(
                result,
                np.full((1, 2, 3),
                        (5 - prg.next_value((1, 2, 3)))) / PLAINTEXT_MULTIPLE))

    def test_should_success_accumulate_and_decrypt_with_dict(self):
        prg = PseudorandomGenerator(1234)
        self.__server._b_masks = [PseudorandomGenerator(1234)]
        self.__server._s_uv_masks = [("1", "2", PseudorandomGenerator(1234)),
                                     ("2", "1", PseudorandomGenerator(1234))]
        self.__server._SSAServer__stage = ProtocolStage.CiphertextAggregate
        np_array = np.ones((1, 2, 3), dtype=np.int16)
        ordered_dict1 = OrderedDict()
        ordered_dict1['int'] = 1
        ordered_dict1['float'] = 1.1
        ordered_dict1['array'] = np_array

        ordered_dict2 = OrderedDict()
        ordered_dict2['int'] = 2
        ordered_dict2['float'] = 2.1
        ordered_dict2['array'] = np.full((1, 2, 3), 2)
        self.__server.ciphertext_accumulate(ordered_dict1, '1')
        result = self.__server.ciphertext_accumulate(ordered_dict2, '2')
        self.assertEqual(result['int'], 3)
        self.assertEqual(result['float'], 3.2)
        self.assertTrue(self.__equal(result['array'], np.full((1, 2, 3), 3)))

        result = self.__server._SSAServer__do_decrypt()
        self.assertEqual(result['int'],
                         (3 - prg.next_value()) / PLAINTEXT_MULTIPLE)
        self.assertEqual(result['float'],
                         (3.2 - prg.next_value()) / PLAINTEXT_MULTIPLE)
        self.assertTrue(
            self.__equal(
                result['array'],
                np.full((1, 2, 3),
                        (3 - prg.next_value((1, 2, 3))) / PLAINTEXT_MULTIPLE)))

    def test_reconstruct_encrypted_shares(self):
        # no drop client
        encrypted_shares_s = {}
        for index1 in range(1, 5):
            encrypted_shares = EncryptedShares()
            for index2 in range(1, 5):
                if index1 == index2:
                    continue
                data = str(index1) + str(index2)
                encrypted_share = EncryptedShare(client_id=str(index2),
                                                 data=data.encode())
                encrypted_shares.encrypted_share.append(encrypted_share)
            encrypted_shares_s[str(index1)] = encrypted_shares

        self.__server._SSAServer__encrypted_shares = encrypted_shares_s
        new = self.__server._SSAServer__reconstruct_encrypted_shares()
        self.assertEqual(new["2"].encrypted_share[0].data.decode(), '12')
        self.assertEqual(new["2"].encrypted_share[1].data.decode(), '32')
        self.assertEqual(new["2"].encrypted_share[2].data.decode(), '42')

        # 1 drop client
        del encrypted_shares_s["2"]
        self.__server._SSAServer__encrypted_shares = encrypted_shares_s
        new = self.__server._SSAServer__reconstruct_encrypted_shares()
        self.assertEqual(new["2"].encrypted_share[0].data.decode(), '12')
        self.assertEqual(new["2"].encrypted_share[1].data.decode(), '32')
        self.assertEqual(new["2"].encrypted_share[2].data.decode(), '42')
        self.assertEqual(new["3"].encrypted_share[0].data.decode(), '13')
        self.assertEqual(new["3"].encrypted_share[1].data.decode(), '43')

        # 2 drop client
        del encrypted_shares_s["4"]
        self.__server._SSAServer__encrypted_shares = encrypted_shares_s
        new = self.__server._SSAServer__reconstruct_encrypted_shares()
        self.assertEqual(new["2"].encrypted_share[0].data.decode(), '12')
        self.assertEqual(new["2"].encrypted_share[1].data.decode(), '32')
        self.assertEqual(new["3"].encrypted_share[0].data.decode(), '13')
        self.assertEqual(len(new["3"].encrypted_share), 1)

    def test_reconstruct_secret_shares(self):
        # alive client 1 and 3, drop client 2 and 4
        secret_shares1 = SecretShares()
        secret_shares1.b_share.append(SecretShare(client_id='1',
                                                  data='1_1'))
        secret_shares1.b_share.append(SecretShare(client_id='3',
                                                  data='3_1'))
        secret_shares1.s_sk_share.append(SecretShare(client_id='2',
                                                     data='2_1'))
        secret_shares1.s_sk_share.append(SecretShare(client_id='4',
                                                     data='4_1'))
        secret_shares3 = SecretShares()
        secret_shares3.b_share.append(SecretShare(client_id='1',
                                                  data='1_3'))
        secret_shares3.b_share.append(SecretShare(client_id='3',
                                                  data='3_3'))
        secret_shares3.s_sk_share.append(SecretShare(client_id='2',
                                                     data='2_3'))
        secret_shares3.s_sk_share.append(SecretShare(client_id='4',
                                                     data='4_3'))
        secret_shares_s = [secret_shares1, secret_shares3]

        self.__server._SSAServer__secret_shares = secret_shares_s
        (s_sk_shares,
         b_shares) = self.__server._SSAServer__reconstruct_secret_shares()
        self.assertEqual(s_sk_shares["2"], ["2_1", "2_3"])
        self.assertEqual(s_sk_shares["4"], ["4_1", "4_3"])
        self.assertEqual(b_shares["1"], ["1_1", "1_3"])
        self.assertEqual(b_shares["3"], ["3_1", "3_3"])

    def __equal(self, array1, array2):
        for index, value in enumerate(array1):
            result = abs(value - array2[index]) < 0.000001
            if not result.all():
                return False
        return True


if __name__ == "__main__":
    unittest.main()
