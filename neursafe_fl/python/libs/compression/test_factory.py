#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=missing-class-docstring, missing-function-docstring
"""
Test compression algorithm creation.
"""

import unittest
from neursafe_fl.python.libs.compression.quantization import \
    QuantizationCompression
from neursafe_fl.python.libs.compression.subsampling import \
    SubsamplingCompression
from neursafe_fl.python.libs.compression.factory import create_compression


class TestFactory(unittest.TestCase):

    def test_create_quantization_compression_successfully(self):
        compression = create_compression("quantization",
                                         **{"quantization_bits": 2})

        self.assertTrue(isinstance(compression, QuantizationCompression))

    def test_create_subsampling_compression_successfully(self):
        compression = create_compression("subsampling",
                                         **{"sampling_rate": 0.5})

        self.assertTrue(isinstance(compression, SubsamplingCompression))


if __name__ == '__main__':
    unittest.main()
