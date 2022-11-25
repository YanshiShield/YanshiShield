#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=missing-class-docstring, missing-function-docstring
# pylint:disable=too-many-function-args
"""Test selective masking compression algorithm.
"""
import unittest

import numpy as np

from neursafe_fl.python.libs.compression.selective_masking import \
    SelectiveMasking


class TestSelectiveMasking(unittest.TestCase):

    def setUp(self) -> None:
        np.random.seed(seed=100)
        self.value = np.random.rand(4, 4, 4)

    def test_raise_exception_if_top_k_ratio_not_correct(self):
        # Top k ratio is not float
        self.assertRaises(ValueError, SelectiveMasking, "0.5")

        # Top k ratio is 1.0
        self.assertRaises(ValueError, SelectiveMasking, 1.0)

        # Top k ratio is 0.0
        self.assertRaises(ValueError, SelectiveMasking, 0.0)

    def test_encode_and_decode_successfully(self):
        compression = SelectiveMasking(0.1)

        masked_value, params = compression.encode(self.value)

        value = compression.decode(masked_value, **params)

        self.assertEqual(np.sort(masked_value)[::-1].tolist(),
                         np.sort(self.value.flatten())[::-1][:6].tolist())

        self.assertEqual(params["shape"], self.value.shape)
        self.assertEqual(params["ind"].sort(),
                         self.value.flatten().argsort()[-6:].tolist().sort())
        self.assertEqual(len(params["ind"]), 6)

        self.assertEqual(np.sort(value.flatten())[::-1][:6].tolist(),
                         np.sort(self.value.flatten())[::-1][:6].tolist())
        self.assertEqual(self.value.shape, value.shape)

        for ind in params["ind"]:
            self.assertEqual(self.value.flatten()[ind],
                             value.flatten()[ind])

    def test_encode_successfully_if_all_values_equal(self):
        value = np.ones(27).reshape(3, 3, 3)
        compression = SelectiveMasking(0.2)

        masked_value, params = compression.encode(value)

        self.assertEqual(params["shape"], value.shape)
        self.assertEqual(masked_value.tolist(), np.ones(5).tolist())
        self.assertEqual(len(params["ind"]), 5)

        value_ = compression.decode(masked_value, **params)

        self.assertEqual(np.sum(value_), 5)
        self.assertEqual(value_.shape, value.shape)

        for ind in params["ind"]:
            self.assertEqual(value_.flatten()[ind],
                             value.flatten()[ind])

    def test_encode_successfully_if_all_values_are_zero(self):
        value = np.zeros(27).reshape(3, 3, 3)
        compression = SelectiveMasking(0.6)

        masked_value, params = compression.encode(value)

        self.assertEqual(params["shape"], value.shape)
        self.assertEqual(masked_value.tolist(), np.zeros(16).tolist())
        self.assertEqual(len(params["ind"]), 16)

        value_ = compression.decode(masked_value, **params)

        self.assertEqual(value_.tolist(), value.tolist())

    def test_encode_successfully_if_top_k_value_is_zero(self):
        value = np.zeros(27).reshape(3, 3, 3)
        compression = SelectiveMasking(0.01)

        masked_value, params = compression.encode(value)

        self.assertEqual(params["shape"], value.shape)
        self.assertEqual(len(params["ind"]), 27)
        self.assertEqual(masked_value.tolist(), np.zeros(27).tolist())

        value_ = compression.decode(masked_value, **params)

        self.assertEqual(value_.tolist(), value.tolist())


if __name__ == '__main__':
    unittest.main()
