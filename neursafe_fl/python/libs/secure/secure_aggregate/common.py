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


def gen_valid_seed(seed):
    """
    Generate valid seed for numpy.
    """
    if seed > MAX_SEED_VALUE:
        return seed % MAX_SEED_VALUE

    return seed


class PseudorandomGenerator:
    """A pseudorandom generator."""
    def __init__(self, seed, return_type='float'):
        self.__seed = gen_valid_seed(seed)
        self.__return_type = return_type

    def next_value(self, shape=(1,)):
        """
        Next pseudorandom array.

        Args:
            shape: the shape of random array to be generated.
        """

        np.random.seed(seed=self.__seed)

        if isinstance(shape, int):
            shape = (shape,)

        if self.__return_type == 'float':
            return np.random.rand(*shape)

        return np.random.randint(-1000, 1000, shape)
