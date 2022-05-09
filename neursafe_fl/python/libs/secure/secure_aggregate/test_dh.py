#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=missing-function-docstring
"""
UnitTest of DiffieHellman key exchange algorithm.
"""
import unittest

from neursafe_fl.python.libs.secure.secure_aggregate.dh import DiffieHellman


class TestDH(unittest.TestCase):
    """Test class of DiffieHellman key exchange algorithm.
    """

    def test_should_exchange_key(self):
        diffe_hellman1 = DiffieHellman()
        diffe_hellman2 = DiffieHellman()
        private1, public1 = diffe_hellman1.generate()
        private2, public2 = diffe_hellman2.generate()

        key1 = diffe_hellman1.agree(private1, public2)
        key2 = diffe_hellman2.agree(private2, public1)

        self.assertEqual(key1, key2)


if __name__ == "__main__":
    unittest.main()
