#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=missing-function-docstring, no-member
"""UnitTest of Pytroch weights calculator.
"""
import unittest
from collections import OrderedDict

import torch

from neursafe_fl.python.runtime.pytorch.weights import PytorchWeightsCalculator


class TestTfWeights(unittest.TestCase):
    """Test class of Pytorch weights calculator.
    """
    def setUp(self):
        self.__pytorch_cw = PytorchWeightsCalculator()

    def test_add_success(self):
        data1 = OrderedDict()
        data1["name1"] = torch.full((2, 2, 3), 1.1)
        data1["name2"] = torch.full((2, 1, 2), 2.2)

        data2 = OrderedDict()
        data2["name1"] = data1["name1"] * 2
        data2["name2"] = data1["name2"] * 2

        result = self.__pytorch_cw.add(data1, data2)
        self.__assert_tensor_equal(result["name1"], torch.full((2, 2, 3), 3.3))
        self.__assert_tensor_equal(result["name2"], torch.full((2, 1, 2), 6.6))

    def test_subtract_success(self):
        data1 = OrderedDict()
        data1["name1"] = torch.full((2, 2, 3), 1.1)
        data1["name2"] = torch.full((2, 1, 2), 2.2)

        data2 = OrderedDict()
        data2["name1"] = data1["name1"] * 2
        data2["name2"] = data1["name2"] * 2

        result = self.__pytorch_cw.subtract(data1, data2)
        self.__assert_tensor_equal(result["name1"], torch.full((2, 2, 3), -1.1))
        self.__assert_tensor_equal(result["name2"], torch.full((2, 1, 2), -2.2))

    def test_multiply_success(self):
        data1 = OrderedDict()
        data1["name1"] = torch.full((2, 2, 3), 1.1)
        data1["name2"] = torch.full((2, 1, 2), 2.2)

        result = self.__pytorch_cw.multiply(data1, 2)
        self.__assert_tensor_equal(result["name1"], torch.full((2, 2, 3), 2.2))
        self.__assert_tensor_equal(result["name2"], torch.full((2, 1, 2), 4.4))

    def test_true_divide_success(self):
        data1 = OrderedDict()
        data1["name1"] = torch.full((2, 2, 3), 1.1)
        data1["name2"] = torch.full((2, 1, 2), 2.2)

        result = self.__pytorch_cw.true_divide(data1, 2)
        self.__assert_tensor_equal(result["name1"], torch.full((2, 2, 3), 0.55))
        self.__assert_tensor_equal(result["name2"], torch.full((2, 1, 2), 1.1))

    def test_equal_success(self):
        data1 = OrderedDict()
        data1["name1"] = torch.full((2, 2, 3), 1.1)
        data1["name2"] = torch.full((2, 1, 2), 2.2)

        data2 = OrderedDict()
        data2["name1"] = data1["name1"] * 2
        data2["name2"] = data1["name2"] * 2

        self.assertFalse(self.__pytorch_cw.equal(data1, data2))

        result = self.__pytorch_cw.subtract(data2, data1)
        self.assertTrue(self.__pytorch_cw.equal(result, data1))

    def __assert_tensor_equal(self, array1, array2):
        result = abs(array1 - array2) < 0.000001
        self.assertTrue(result.all())


if __name__ == '__main__':
    unittest.main()
