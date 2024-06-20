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

        self.assertEqual(prg.next_value().tolist(), [5682])
        self.assertEqual(prg.next_value(1).tolist(), [7290])
        self.assertEqual(prg.next_value(5).tolist(),
                         [8840, 7570, 3760, 4629, 586])
        self.assertEqual(prg.next_value((5,)).tolist(),
                         [404, 6301, 6154, 4143, 4134])

        self.assertEqual(prg.next_value((2, 2)).tolist(),
                         [[197, 4576], [180, 7013]])


if __name__ == "__main__":
    unittest.main()
