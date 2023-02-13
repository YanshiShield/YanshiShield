#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-few-public-methods
"""The common lib for secure aggreagtor
"""

from enum import Enum
import numpy as np

MAX_SEED_VALUE = 2 ** 32 - 1
PLAINTEXT_MULTIPLE = 10240


class ProtocolStage(Enum):
    """Round state.
    """
    ExchangePublicKey = 0
    ExchangeEncryptedShare = 1
    CiphertextAggregate = 2
    DecryptResult = 3


def can_be_added(data):
    """Can data be added.
    """
    return hasattr(data, '__add__')


def get_shape(data):
    """
    Return data shape
    """
    default_shape = (1,)

    if hasattr(data, "shape"):
        return data.shape

    return default_shape


class PseudorandomGenerator:
    """A pseudorandom generator."""
    def __init__(self, seed):
        self.__random = np.random.default_rng(seed)

    def next_value(self, shape=(1,)):
        """
        Next pseudorandom array.

        Args:
            shape: the shape of random array to be generated.
        """
        if isinstance(shape, int):
            shape = (shape,)

        return self.__random.integers(0, 10000, shape)
