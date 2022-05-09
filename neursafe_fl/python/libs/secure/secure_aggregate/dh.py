#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=invalid-name
"""DiffieHellman key exchange algorithm

reference:
https://github.com/AlexConnat/SecureAggregation/blob/master/diffie_hellman.py
"""
import os
from diffiehellman.primes import PRIMES


class DiffieHellman:
    """Implement Diffie Hellman key exchange algorithm.
    """
    def __init__(self, groupID=14):
        self.__g = PRIMES[groupID]['generator']
        self.__p = PRIMES[groupID]['prime']

    def generate(self):
        """Generate private key and public key.
        """
        sk = int.from_bytes(os.urandom(128), 'big')
        pk = pow(self.__g, sk, self.__p)
        return sk, pk

    def agree(self, sk, pk):
        """Negotiate generate shared secret.
        """
        shared_key = pow(pk, sk, self.__p)
        return shared_key
