#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""
Creation factory of different compression algorithm instance.
"""

from neursafe_fl.python.libs.compression.quantization import \
    QuantizationCompression
from neursafe_fl.python.libs.compression.subsampling import \
    SubsamplingCompression
from neursafe_fl.python.libs.compression.selective_masking import \
    SelectiveMasking


def create_compression(name, **kwargs):
    """
    Create specified compression algorithm instance.
    """
    compression_map = {"quantization": QuantizationCompression,
                       "subsampling": SubsamplingCompression,
                       "selective_masking": SelectiveMasking}

    return compression_map[name](**kwargs)
