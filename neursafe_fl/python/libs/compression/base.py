#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""
Compression algorithm base class definition.
"""

import abc


class Compression:
    """
    Compression algorithm base class.
    """

    @abc.abstractmethod
    def encode(self, *args, **kwargs):
        """Encode data(compress data).
        """

    @abc.abstractmethod
    def decode(self, *args, **kwargs):
        """Decode data(recover from compressed data).
        """
