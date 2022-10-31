# -*- coding: utf-8 -*-
# pylint:disable=missing-class-docstring, missing-function-docstring
# pylint:disable=protected-access, invalid-name
"""
"""
import unittest
import importlib
import numpy as np

import neursafe_fl.python.runtime.operation as op


class ComputationTest(unittest.TestCase):

    # Test executing ops in tensorflow
    def test_floor_div_in_tf(self):
        op._runtime = importlib.import_module("tensorflow")
        op.floor_div = op._floor_div_in_tf

        # x: numpy.ndarray, y: int
        x = np.array([[1], [2], [3]], dtype=np.int32)
        x = np.reshape(x, [-1, 1])
        res = op.floor_div(x, 2)

        self.assertEqual(res.dtype, np.int32)
        self.assertEqual(res.numpy().tolist(), [[0], [1], [1]])

        # x: numpy.ndarray, y: numpy.ndarry
        x = np.array([[1], [2], [3]], dtype=np.int32)
        x = np.reshape(x, [-1, 1])
        y = np.array([1, 2], dtype=np.int32)
        res = op.floor_div(x, y)

        self.assertEqual(res.dtype, np.int32)
        self.assertEqual(res.numpy().tolist(), [[1, 0], [2, 1], [3, 1]])

    def test_mod_in_tf(self):
        op._runtime = importlib.import_module("tensorflow")
        op.mod = op._mod_in_tf

        # x: numpy.ndarray, y: int
        x = np.array([1, 2, 3], dtype=np.int32)
        res = op.mod(x, 2)

        self.assertEqual(res.dtype, np.int32)
        self.assertEqual(res.numpy().tolist(), [1, 0, 1])

        # x: numpy.ndarray, y: numpy.ndarray
        x = np.array([1, 2, 3], dtype=np.int32)
        y = np.array([2, 1, 1], dtype=np.int32)
        res = op.mod(x, y)

        self.assertEqual(res.dtype, np.int32)
        self.assertEqual(res.numpy().tolist(), [1, 0, 0])

    def test_concatenate_in_tf(self):
        op._runtime = importlib.import_module("tensorflow")
        op.concatenate = op._concatenate_in_tf

        x = np.array([1, 2, 3], dtype=np.int32)
        y = np.array([2, 1, 1], dtype=np.int32)
        res = op.concatenate(x, y)

        self.assertEqual(res.dtype, np.int32)
        self.assertEqual(res.numpy().tolist(), [1, 2, 3, 2, 1, 1])

    # Test executing ops in pytorch
    def test_floor_div_in_torch(self):
        op._runtime = importlib.import_module("torch")
        op.floor_div = op._floor_div_in_torch

        # x: numpy.ndarray, y: int
        x = np.array([[1], [2], [3]], dtype=np.int32)
        x = np.reshape(x, [-1, 1])
        res = op.floor_div(x, 2)

        self.assertEqual(res.dtype, np.int32)
        self.assertEqual(res.tolist(), [[0], [1], [1]])

        # x: numpy.ndarray, y: numpy.ndarry
        x = np.array([[1], [2], [3]], dtype=np.int32)
        x = np.reshape(x, [-1, 1])
        y = np.array([1, 2], dtype=np.int32)
        res = op.floor_div(x, y)

        self.assertEqual(res.dtype, np.int32)
        self.assertEqual(res.tolist(), [[1, 0], [2, 1], [3, 1]])

    def test_mod_in_torch(self):
        op._runtime = importlib.import_module("torch")
        op.mod = op._mod_in_torch

        # x: numpy.ndarray, y: int
        x = np.array([1, 2, 3], dtype=np.int32)
        res = op.mod(x, 2)

        self.assertEqual(res.dtype, np.int32)
        self.assertEqual(res.tolist(), [1, 0, 1])

        # x: numpy.ndarray, y: numpy.ndarray
        x = np.array([1, 2, 3], dtype=np.int32)
        y = np.array([2, 1, 1], dtype=np.int32)
        res = op.mod(x, y)

        self.assertEqual(res.dtype, np.int32)
        self.assertEqual(res.tolist(), [1, 0, 0])

    def test_concatenate_in_torch(self):
        op._runtime = importlib.import_module("torch")
        op.concatenate = op._concatenate_in_torch

        x = np.array([1, 2, 3], dtype=np.int32)
        y = np.array([2, 1, 1], dtype=np.int32)
        res = op.concatenate(x, y)

        self.assertEqual(res.dtype, np.int32)
        self.assertEqual(res.tolist(), [1, 2, 3, 2, 1, 1])


if __name__ == '__main__':
    unittest.main()
