#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=missing-function-docstring
"""
UnitTest of DiffieHellman key exchange algorithm.
"""
import unittest
from neursafe_fl.python.libs.secure.secure_aggregate.common import \
    PseudorandomGenerator


class TestCommon(unittest.TestCase):
    """Test some function in common.
    """
    def test_prg(self):
        prg = PseudorandomGenerator(6532444414)
        self.assertEqual("{:04.3f}".format(prg.next_number()), "0.407")
        self.assertEqual("{:04.3f}".format(prg.next_number()), "0.801")
        self.assertEqual("{:04.3f}".format(prg.next_number()), "0.035")


if __name__ == "__main__":
    unittest.main()
