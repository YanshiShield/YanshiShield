#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-few-public-methods
"""The common lib for secure aggreagtor
"""

from enum import Enum
import numpy as np

MAX_SEED_VALUE = 2 ** 32 - 1


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
    def __init__(self, seed, return_type='float'):
        self.__random = np.random.default_rng(seed)
        self.__return_type = return_type

    def next_value(self, shape=(1,)):
        """
        Next pseudorandom array.

        Args:
            shape: the shape of random array to be generated.
        """
        if isinstance(shape, int):
            shape = (shape,)

        if self.__return_type == 'float':
            return self.__random.random(shape)

        return self.__random.integers(-1000, 1000, shape)
