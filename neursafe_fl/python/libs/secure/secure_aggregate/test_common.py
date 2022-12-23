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

        def format_float(array):
            return [float("{:04.3f}".format(value)) for value in array]

        self.assertEqual(format_float(prg.next_value()), [0.729])
        self.assertEqual(format_float(prg.next_value(1)), [0.757])
        self.assertEqual(format_float(prg.next_value(5)),
                         [0.463, 0.04, 0.615, 0.413, 0.458])
        self.assertEqual(format_float(prg.next_value((5,))),
                         [0.701, 0.884, 0.688, 0.782, 0.14])

        self.assertEqual([format_float(value) for value in prg.next_value((2, 2))],
                         [[0.4, 0.197], [0.405, 0.591]])

        prg = PseudorandomGenerator(6532444414, return_type="int")

        self.assertEqual(prg.next_value().tolist(), [136])
        self.assertEqual(prg.next_value(1).tolist(), [458])
        self.assertEqual(prg.next_value(5).tolist(),
                         [768, 514, -248, -75, -883])
        self.assertEqual(prg.next_value((5,)).tolist(),
                         [-920, 260, 230, -172, -174])

        self.assertEqual(prg.next_value((2, 2)).tolist(),
                         [[-961, -85], [-964, 402]])


if __name__ == "__main__":
    unittest.main()
