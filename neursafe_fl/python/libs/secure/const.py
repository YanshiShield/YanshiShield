#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
const variable in secure algorithm.
"""

from enum import Enum


class SecureAlgorithm(Enum):
    """Supported secure algorithms"""

    dp = "DP"
    ssa = "SSA"


SUPPORTED_SECURE_ALGORITHM = [
    algorithm.value for algorithm in SecureAlgorithm]
