#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=invalid-name

"""
Due to poor performance of some ops of numpy, the relevant ops are executed by
the underlying runtime.

Abstracts some mathematical operation methods in different runtimes, which is
convenient for upper modules to call, and has no awareness of the underlying
runtimes, current support underlying runtimes are tensorflow and pytorch.
"""

import importlib
import numpy as np


# Tensorflow runtime
def _floor_div_in_tf(x: np.ndarray, y: [np.ndarray, int]):
    return _runtime.math.floordiv(x, y)


def _mod_in_tf(x: np.ndarray, y: [np.ndarray, int]):
    return _runtime.math.mod(x, y)


def _concatenate_in_tf(x: np.ndarray, y: np.ndarray, axis=0):
    return _runtime.concat([x, y], axis)


# Pytorch runtime
def _floor_div_in_torch(x: np.ndarray, y: [np.ndarray, int]):
    x = _runtime.from_numpy(x)

    if isinstance(y, np.ndarray):
        y = _runtime.from_numpy(y)

    return _runtime.floor_divide(x, y).numpy()


def _mod_in_torch(x: np.ndarray, y: [np.ndarray, int]):
    x = _runtime.from_numpy(x)

    if isinstance(y, np.ndarray):
        y = _runtime.from_numpy(y)

    return _runtime.fmod(x, y).numpy()


def _concatenate_in_torch(x: np.ndarray, y: np.ndarray, axis=0):
    x = _runtime.from_numpy(x)
    y = _runtime.from_numpy(y)

    return _runtime.cat([x, y], axis).numpy()


try:
    _runtime = importlib.import_module("tensorflow")
    floor_div = _floor_div_in_tf
    mod = _mod_in_tf
    concatenate = _concatenate_in_tf
except ModuleNotFoundError:
    _runtime = importlib.import_module("torch")
    floor_div = _floor_div_in_torch
    mod = _mod_in_torch
    concatenate = _concatenate_in_torch
