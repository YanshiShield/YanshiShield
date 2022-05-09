#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=missing-function-docstring
"""UnitTest of TF weights calculator.
"""
import unittest
import numpy as np

from neursafe_fl.python.runtime.tensorflow.weights import TensorflowWeightsCalculator


class TestTfWeights(unittest.TestCase):
    """Test class of TF weights calculator.
    """
    def setUp(self):
        self.__tf_wc = TensorflowWeightsCalculator()

    def test_add_success(self):
        origin_data1 = np.full((2, 2, 3), 1.1)
        origin_data2 = np.full((2, 1, 2), 2.2)
        data1 = [origin_data1, origin_data2]
        data2 = [np.multiply(origin_data1, 2),
                 np.multiply(origin_data2, 2)]

        result = self.__tf_wc.add(data1, data2)
        self.__assert_ndarray_equal(result[0], np.full((2, 2, 3), 3.3))
        self.__assert_ndarray_equal(result[1], np.full((2, 1, 2), 6.6))

    def test_subtract_success(self):
        origin_data1 = np.full((2, 2, 3), 1.1)
        origin_data2 = np.full((2, 1, 2), 2.2)
        data1 = [origin_data1, origin_data2]
        data2 = [np.multiply(origin_data1, 2),
                 np.multiply(origin_data2, 2)]

        result = self.__tf_wc.subtract(data1, data2)
        self.__assert_ndarray_equal(result[0], np.full((2, 2, 3), -1.1))
        self.__assert_ndarray_equal(result[1], np.full((2, 1, 2), -2.2))

    def test_multiply_success(self):
        origin_data1 = np.full((2, 2, 3), 1.1)
        origin_data2 = np.full((2, 1, 2), 2.2)
        data1 = [origin_data1, origin_data2]

        result = self.__tf_wc.multiply(data1, 2)
        self.__assert_ndarray_equal(result[0], np.full((2, 2, 3), 2.2))
        self.__assert_ndarray_equal(result[1], np.full((2, 1, 2), 4.4))

    def test_true_divide(self):
        origin_data1 = np.full((2, 2, 3), 1.1)
        origin_data2 = np.full((2, 1, 2), 2.2)
        data1 = [origin_data1, origin_data2]

        result = self.__tf_wc.true_divide(data1, 2)
        self.__assert_ndarray_equal(result[0], np.full((2, 2, 3), 0.55))
        self.__assert_ndarray_equal(result[1], np.full((2, 1, 2), 1.1))

    def test_equal_success(self):
        origin_data1 = np.full((2, 2, 3), 1.1)
        origin_data2 = np.full((2, 1, 2), 2.2)
        data1 = [origin_data1, origin_data2]
        data2 = [np.multiply(origin_data1, 2),
                 np.multiply(origin_data2, 2)]

        self.assertFalse(self.__tf_wc.equal(data1, data2))

        result = self.__tf_wc.subtract(data2, data1)
        self.assertTrue(self.__tf_wc.equal(data1, result))

    def __assert_ndarray_equal(self, array1, array2):
        result = abs(array1 - array2) < 0.000001
        self.assertTrue(result.all())


if __name__ == '__main__':
    unittest.main()
