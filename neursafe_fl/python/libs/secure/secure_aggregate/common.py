#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-few-public-methods
"""The common lib for secure aggreagtor
"""
import random
from enum import Enum


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


class PseudorandomGenerator:
    """A pseudorandom generator."""
    def __init__(self, seed, return_type='float'):
        self.__random = random.Random(seed)
        self.__return_type = return_type

    def next_number(self):
        """Next pseudorandom number."""
        if self.__return_type == 'float':
            return self.__random.random()
        return self.__random.randint(-1000, 1000)
