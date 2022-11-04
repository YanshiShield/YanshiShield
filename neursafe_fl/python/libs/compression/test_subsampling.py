#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=missing-class-docstring, missing-function-docstring
# pylint:disable=too-many-function-args
"""Test subsampling compress algorithm.
"""

import unittest

import numpy as np

from neursafe_fl.python.libs.compression.subsampling import \
    SubsamplingCompression


class TestSubsampling(unittest.TestCase):

    def setUp(self) -> None:
        self.value = np.array([(i + 1) * 1.0 for i in range(16)]).reshape(
            2, 2, 4)
        self.shape = self.value.shape

    def test_raise_exception_if_sampling_rate_not_correct(self):
        # Sampling rate is not float
        self.assertRaises(ValueError, SubsamplingCompression, "0.5")

        # Sampling rate is 1.0
        self.assertRaises(ValueError, SubsamplingCompression, 1.0)

        # Sampling rate is 0.0
        self.assertRaises(ValueError, SubsamplingCompression, 0.0)

    def assert_result_correct(self, compression):
        encoded, params = compression.encode(self.value)

        decoded = compression.decode(encoded, **params)

        self.assertEqual(params["shape"], self.shape)
        self.assertEqual(np.sum(encoded), np.sum(decoded))
        self.assertEqual(encoded.size, np.count_nonzero(decoded))

    def test_encode_and_decode_correctly_if_sampling_rate_is_30(self):
        compression = SubsamplingCompression(0.3)

        self.assert_result_correct(compression)

    def test_encode_and_decode_correctly_if_sampling_rate_is_50(self):
        compression = SubsamplingCompression(0.5)

        self.assert_result_correct(compression)

    def test_encode_and_decode_correctly_if_sampling_rate_is_80(self):
        compression = SubsamplingCompression(0.8)

        self.assert_result_correct(compression)


if __name__ == '__main__':
    unittest.main()
