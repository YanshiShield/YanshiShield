#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint: disable=missing-function-docstring, missing-module-docstring
# pylint: disable=missing-class-docstring, too-many-function-args
"""
test dp generator.
"""
import unittest
import numpy as np
from neursafe_fl.python.libs.secure.differential_privacy.dp_generator import DPGenerator
from neursafe_fl.python.libs.secure.differential_privacy.errors import DPGeneratorError


class TestDPGenerator(unittest.TestCase):

    def setUp(self):
        self.__dp_generator = DPGenerator(4.0)

    def test_add_same_noise_successfully(self):
        protection_data = np.array([0, 0, 0, 0, 0, 0, 0, 0],
                                   dtype=float).reshape(2, 2, 2)
        noised_data = self.__dp_generator.add_noise(protection_data)
        self.assertEqual(noised_data[0][0][0], noised_data[0][0][1])
        self.assertEqual(noised_data[0][1][0], noised_data[0][1][1])

    def test_add_different_noise_successfully(self):
        protection_data = np.array([0, 0, 0, 0, 0, 0, 0, 0],
                                   dtype=float).reshape(2, 2, 2)
        noised_data = self.__dp_generator.add_noise(protection_data,
                                                    adding_same_noise=False)
        self.assertFalse(noised_data[0][0][0] == noised_data[0][0][1])
        self.assertFalse(noised_data[0][1][0] == noised_data[0][1][1])

    def test_compute_privacy_spent_successfully(self):
        # stpes = 0
        self.assertRaises(DPGeneratorError,
                          self.__dp_generator.compute_privacy_spent, 0)

        # steps = 1
        privacy_spent_1 = self.__dp_generator.compute_privacy_spent(1)

        # steps = 2
        privacy_spent_2 = self.__dp_generator.compute_privacy_spent(2)

        self.assertTrue(privacy_spent_2 > privacy_spent_1)

        # steps = 1000
        privacy_spent_1000 = self.__dp_generator.compute_privacy_spent(1000)
        self.assertTrue(privacy_spent_1000 < 1000 * privacy_spent_1)

    def test_add_noise_if_protection_data_is_not_ndarray(self):
        self.assertRaises(DPGeneratorError, self.__dp_generator.add_noise, 1)


if __name__ == "__main__":
    unittest.main()
