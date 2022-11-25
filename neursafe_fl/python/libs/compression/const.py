#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
const variable in compression algorithm.
"""
from enum import Enum


class CompressionAlgorithm(Enum):
    """Suppport compress algorithms"""

    quantization = "QUANTIZATION"
    subsampling = "SUBSAMPLING"
    selectivemasking = "SELECTIVE_MASKING"


SUPPORTED_COMPRESSION_ALGORITHM = [
    algorithm.value for algorithm in CompressionAlgorithm]
