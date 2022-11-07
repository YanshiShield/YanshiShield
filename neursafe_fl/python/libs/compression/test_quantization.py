#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=missing-class-docstring, missing-function-docstring
# pylint:disable=too-many-function-args
"""Test quantization compress algorithm.
"""


import unittest
import numpy as np

from neursafe_fl.python.libs.compression.quantization import \
    QuantizationCompression


class TestQuantization(unittest.TestCase):

    def setUp(self):
        self.value = np.array([i * 1.0 for i in range(16)]).reshape(2, 2, 4)
        self.max = np.max(self.value)
        self.min = np.min(self.value)

    def test_raise_exception_if_quantization_bits_not_correct(self):
        # Quantization_bits not int
        self.assertRaises(ValueError, QuantizationCompression, "a")

        # Quantization_bits less than 2
        self.assertRaises(ValueError, QuantizationCompression, 1)

        # Quantization_bits more than 16
        self.assertRaises(ValueError, QuantizationCompression, 17)

    def test_quantization_bits_is_2(self):
        compression = QuantizationCompression(2)

        # Quantify successfully
        res = compression.quantify(self.value)
        self.assertEqual(res.dtype, np.int32)
        self.assertEqual(res.tolist(), [[[0, 0, 0, 1], [1, 1, 1, 1]],
                                        [[2, 2, 2, 2], [2, 3, 3, 3]]])

        # Pack successfully
        res = compression.pack_into_int(res)
        self.assertEqual(res.dtype, np.int32)
        self.assertEqual(res.tolist(), [[2125092160], [1]])

        # Unpack successfully
        res = compression.unpack_into_int(res,
                                          self.value.shape)
        self.assertEqual(res.tolist(), [[[0, 0, 0, 1], [1, 1, 1, 1]],
                                        [[2, 2, 2, 2], [2, 3, 3, 3]]])

        # Unquantify successfully
        res = compression.unquantify(res, self.max, self.min)
        self.assertEqual(res.dtype, np.float64)
        self.assertEqual(res.tolist(),
                         [[[0.0, 0.0, 0.0, 5.0], [5.0, 5.0, 5.0, 5.0]],
                          [[10.0, 10.0, 10.0, 10.0], [10.0, 15.0, 15.0, 15.0]]])

    def test_quantization_bits_is_4(self):
        compression = QuantizationCompression(4)

        # Quantify successfully
        res = compression.quantify(self.value)
        self.assertEqual(res.dtype, np.int32)
        self.assertEqual(res.tolist(), [[[0, 1, 2, 3], [4, 5, 6, 7]],
                                        [[8, 9, 10, 11], [12, 13, 14, 15]]])

        # Pack successfully
        res = compression.pack_into_int(res)
        self.assertEqual(res.dtype, np.int32)
        self.assertEqual(res.tolist(), [[1985229328], [2109306160], [3]])

        # Unpack successfully
        res = compression.unpack_into_int(res,
                                          self.value.shape)
        self.assertEqual(res.tolist(), [[[0, 1, 2, 3], [4, 5, 6, 7]],
                                        [[8, 9, 10, 11], [12, 13, 14, 15]]])

        # Unquantify successfully
        res = compression.unquantify(res, self.max, self.min)
        self.assertEqual(res.dtype, np.float64)
        self.assertEqual(res.tolist(),
                         [[[0.0, 1.0, 2.0, 3.0], [4.0, 5.0, 6.0, 7.0]],
                          [[8.0, 9.0, 10.0, 11.0], [12.0, 13.0, 14.0, 15.0]]])

    def test_quantization_bits_is_8(self):
        compression = QuantizationCompression(8)

        # Quantify successfully
        res = compression.quantify(self.value)
        self.assertEqual(res.dtype, np.int32)
        self.assertEqual(res.tolist(),
                         [[[0, 17, 34, 51], [68, 85, 102, 119]],
                          [[136, 153, 170, 187], [204, 221, 238, 255]]])

        # Pack successfully
        res = compression.pack_into_int(res)
        self.assertEqual(res.dtype, np.int32)
        self.assertEqual(res.tolist(),
                         [[857870592], [1858906760], [1856661025], [2138500709], [15]])

        # Unpack successfully
        res = compression.unpack_into_int(res,
                                          self.value.shape)
        self.assertEqual(res.tolist(),
                         [[[0, 17, 34, 51], [68, 85, 102, 119]],
                          [[136, 153, 170, 187], [204, 221, 238, 255]]])

        # Unquantify successfully
        res = compression.unquantify(res, self.max, self.min)
        self.assertEqual(res.dtype, np.float64)
        self.assertEqual(res.tolist(),
                         [[[0.0, 1.0, 2.0, 3.0], [4.0, 5.0, 6.0, 7.0]],
                          [[8.0, 9.0, 10.0, 11.0], [12.0, 13.0, 14.0, 15.0]]])

    def test_encode_and_decode_successfully_if_bits_is_2(self):
        compression = QuantizationCompression(2)

        # Encode
        res, params = compression.encode(self.value)
        self.assertEqual(params, {"max_value": 15.0,
                                  "min_value": 0.0,
                                  "shape": (2, 2, 4)})
        self.assertEqual(res.dtype, np.int32)
        self.assertEqual(res.tolist(), [[2125092160], [1]])

        # Encode
        res = compression.decode(res, **params)
        self.assertEqual(res.dtype, np.float64)
        self.assertEqual(res.tolist(),
                         [[[0.0, 0.0, 0.0, 5.0], [5.0, 5.0, 5.0, 5.0]],
                          [[10.0, 10.0, 10.0, 10.0], [10.0, 15.0, 15.0, 15.0]]])

    def test_encode_and_decode_successfully_if_bits_is_4(self):
        compression = QuantizationCompression(4)

        # Encode
        res, params = compression.encode(self.value)
        self.assertEqual(params, {"max_value": 15.0,
                                  "min_value": 0.0,
                                  "shape": (2, 2, 4)})
        self.assertEqual(res.dtype, np.int32)
        self.assertEqual(res.tolist(), [[1985229328], [2109306160], [3]])

        # Decode
        res = compression.decode(res, **params)
        self.assertEqual(res.dtype, np.float64)
        self.assertEqual(res.tolist(),
                         [[[0.0, 1.0, 2.0, 3.0], [4.0, 5.0, 6.0, 7.0]],
                          [[8.0, 9.0, 10.0, 11.0], [12.0, 13.0, 14.0, 15.0]]])

    def test_quantify_and_unquantify_successfully_if_array_all_zeros(self):
        value = np.array([0.0 for _ in range(16)]).reshape(2, 2, 4)
        compression = QuantizationCompression(2)

        # Quantify
        res = compression.quantify(value)
        self.assertEqual(res.dtype, np.int32)
        self.assertEqual(res.tolist(), [[[0, 0, 0, 0], [0, 0, 0, 0]],
                                        [[0, 0, 0, 0], [0, 0, 0, 0]]])

        # Unquantify
        res = compression.unquantify(res, np.max(value), np.min(value))
        self.assertEqual(res.dtype, np.float64)
        self.assertEqual(res.tolist(), value.tolist())

    def test_quantify_and_unquantify_successfully_if_array_all_5(self):
        value = np.array([5.0 for _ in range(16)]).reshape(2, 2, 4)
        compression = QuantizationCompression(2)

        # Quantify
        res = compression.quantify(value)
        self.assertEqual(res.dtype, np.int32)
        self.assertEqual(res.tolist(), [[[1, 1, 1, 1], [1, 1, 1, 1]],
                                        [[1, 1, 1, 1], [1, 1, 1, 1]]])

        # Unquantify
        res = compression.unquantify(res, np.max(value), np.min(value))
        self.assertEqual(res.dtype, np.float64)
        self.assertEqual(res.tolist(), value.tolist())


if __name__ == '__main__':
    unittest.main()
