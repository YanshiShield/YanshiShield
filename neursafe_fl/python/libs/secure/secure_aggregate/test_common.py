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

        self.assertEqual(format_float(prg.next_value()), [0.127])
        self.assertEqual(format_float(prg.next_value(1)), [0.127])
        self.assertEqual(format_float(prg.next_value(5)),
                         [0.127, 0.077, 0.52, 0.885, 0.084])
        self.assertEqual(format_float(prg.next_value((5,))),
                         [0.127, 0.077, 0.52, 0.885, 0.084])

        self.assertEqual([format_float(value) for value in prg.next_value((2, 2))],
                         [[0.127, 0.077], [0.52, 0.885]])

        prg = PseudorandomGenerator(6532444414, return_type="int")

        self.assertEqual(prg.next_value().tolist(), [427])
        self.assertEqual(prg.next_value(1).tolist(), [427])
        self.assertEqual(prg.next_value(5).tolist(),
                         [427, 469, -964, -851, -756])
        self.assertEqual(prg.next_value((5,)).tolist(),
                         [427, 469, -964, -851, -756])

        self.assertEqual(prg.next_value((2, 2)).tolist(),
                         [[427, 469], [-964, -851]])


if __name__ == "__main__":
    unittest.main()
