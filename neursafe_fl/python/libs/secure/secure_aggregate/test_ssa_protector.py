#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=missing-function-docstring, protected-access, no-member, invalid-name
"""UnitTest of SSA protector.
"""

from collections import OrderedDict
import unittest

import numpy as np

from neursafe_fl.python.libs.secure.secure_aggregate.ssa_protector import \
    SSAProtector
from neursafe_fl.python.libs.secure.secure_aggregate.common import \
    PseudorandomGenerator


class TestSSAProtector(unittest.TestCase):
    """Test class of SSA protector.
    """
    def setUp(self):
        self.protector = SSAProtector("test", False)

        self.protector.id_ = "my_id"
        self.protector.b = 1234
        self.protector.s_uv_s = [("my_ia", PseudorandomGenerator(1234)),
                                 ("my_ie", PseudorandomGenerator(1234))]

        self.prg = PseudorandomGenerator(1234)

    def test_should_success_encrypt_int(self):
        result = self.protector.encrypt(1)

        self.assertEqual(result, 1 + self.prg.next_value())

    def test_should_success_encrypt_float(self):
        result = self.protector.encrypt(1.123)

        self.assertEqual(result, 1.123 + self.prg.next_value())

    def test_should_success_encrypt_np_array(self):
        np_array = np.ones((1, 2, 3), dtype=np.int16)
        new_array = self.protector.encrypt(np_array)
        self.assertTrue(
            self.__equal(new_array,
                         np.full_like(new_array,
                                      1 + self.prg.next_value(np_array.shape))))

    def test_should_success_encrypt_list(self):
        np_array_list = [np.ones((2, 2, 3), dtype=np.int16),
                         np.full((3, 1, 3), 2)]
        new_array_list = self.protector.encrypt(np_array_list)

        self.assertTrue(self.__equal(
            new_array_list[0],
            np.full((2, 2, 3), 1 + self.prg.next_value((2, 2, 3)))))
        self.assertTrue(self.__equal(
            new_array_list[1],
            np.full_like(new_array_list[1], 2 + self.prg.next_value((3, 1, 3)))))

    def test_should_success_encrypt_dict(self):
        np_array = np.ones((1, 2, 3), dtype=np.int16)
        ordered_dict = OrderedDict()
        ordered_dict['int'] = 1
        ordered_dict['float'] = 1.1
        ordered_dict['array'] = np_array
        new_dict = self.protector.encrypt(ordered_dict)
        self.assertEqual(new_dict['int'], 1 + self.prg.next_value())
        self.assertEqual(new_dict['float'], 1.1 + self.prg.next_value())
        self.assertTrue(self.__equal(
            new_dict['array'],
            np.full_like(new_dict['array'], 1 + self.prg.next_value((1, 2, 3)))))

    def __equal(self, array1, array2):
        for index, value in enumerate(array1):
            result = abs(value - array2[index]) < 0.000001
            if not result.all():
                return False
        return True


if __name__ == "__main__":
    unittest.main()
