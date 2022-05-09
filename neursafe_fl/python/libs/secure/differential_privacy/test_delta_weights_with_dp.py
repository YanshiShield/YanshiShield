# -*- coding: utf-8 -*-

#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint: disable=missing-function-docstring, missing-module-docstring
# pylint: disable=too-many-function-args, missing-class-docstring
import unittest
import numpy as np

from neursafe_fl.python.libs.secure.differential_privacy.dp_delta_weights \
    import DeltaWeightsDP
from neursafe_fl.python.libs.secure.differential_privacy.errors import DPGeneratorError


class TestDeltaWeightsDP(unittest.TestCase):

    def setUp(self):
        self.__weights_list = [np.array([0, 0, 0, 0, 0, 0],
                                        dtype=float).reshape(2, 3),
                               np.array([0, 0, 0, 0, 0, 0, 0, 0],
                                        dtype=float).reshape(2, 2, 2),
                               np.array([0, 0, 0, 0], dtype=float)]
        self.__delta_weights_dp = DeltaWeightsDP(1.0)

    def test_add_same_noise_to_delta_weights_of_all_layers(self):
        noised_weights_list = self.__delta_weights_dp.add_noise_to_all_layers(
            self.__weights_list)
        self.assertEqual(noised_weights_list[0][0][0],
                         noised_weights_list[0][0][1])
        self.assertEqual(noised_weights_list[1][0][0][0],
                         noised_weights_list[1][0][0][1])
        self.assertEqual(noised_weights_list[2][0],
                         noised_weights_list[2][1])

    def test_add_diff_noise_to_delta_weights_of_all_layers(self):
        noised_weights_list = self.__delta_weights_dp.add_noise_to_all_layers(
            self.__weights_list, False)
        self.assertFalse(noised_weights_list[0][0][0]
                         == noised_weights_list[0][0][1])
        self.assertFalse(noised_weights_list[1][0][0][0]
                         == noised_weights_list[1][0][0][1])
        self.assertFalse(noised_weights_list[2][0]
                         == noised_weights_list[2][1])

    def test_add_same_noise_to_delta_weights_of_one_layer(self):
        noised_weights = self.__delta_weights_dp.add_noise_to_one_layer(
            self.__weights_list[2])
        self.assertEqual(noised_weights[0], noised_weights[1])

    def test_add_diff_noise_to_delta_weights_of_one_layer(self):
        noised_weights = self.__delta_weights_dp.add_noise_to_one_layer(
            self.__weights_list[2], False)
        self.assertFalse(noised_weights[0] == noised_weights[1])

    def test_raise_exception_if_delta_weights_list_is_not_list(self):
        self.assertRaises(DPGeneratorError,
                          self.__delta_weights_dp.add_noise_to_all_layers, {})

    def test_raise_exception_if_delta_weights_is_not_ndarray(self):
        self.assertRaises(DPGeneratorError,
                          self.__delta_weights_dp.add_noise_to_one_layer, 1)

    def test_get_privacy_spent_successfully(self):
        # steps = 1
        privacy_spent_1 = self.__delta_weights_dp.get_privacy_spent(1)

        # steps = 2
        privacy_spent_2 = self.__delta_weights_dp.get_privacy_spent(2)

        self.assertTrue(privacy_spent_2 > privacy_spent_1)


if __name__ == "__main__":
    unittest.main()
