#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""
Creation factory of different compression algorithm instance.
"""

from neursafe_fl.python.libs.compression.quantization import \
    QuantizationCompression
from neursafe_fl.python.libs.compression.subsampling import \
    SubsamplingCompression


def create_compression(name, **kwargs):
    """
    Create specified compression algorithm instance.
    """
    compression_map = {"quantization": QuantizationCompression,
                       "subsampling": SubsamplingCompression}

    return compression_map[name](**kwargs)
