#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=invalid-name
"""Optimizer for client sdk.
"""
import os
from absl import logging
from neursafe_fl.python.sdk.utils import get_runtime, TASK_OPTIMIZER, \
    TASK_OPTIMIZER_PARAM


FEDPROX = "fedprox"
SCAFFOLD = "scaffold"


def _create_fedprox(params):
    learning_rate = float(params.get("learning_rate", 0.01))
    mu = float(params.get("mu", 0.6))
    origin_trainable_weights = params.get("origin_trainable_weights", None)

    module_name = "neursafe_fl.python.libs.optimizer.%s.%s" % (
        get_runtime().lower(), FEDPROX)
    module = __import__(module_name, fromlist=True)
    class_name = "PerturbedGradientDescent"
    return getattr(module, class_name)(
        learning_rate=learning_rate,
        mu=mu,
        origin_trainable_weights=origin_trainable_weights)


def _create_scaffold(params=None):
    if params:
        model_params = params.get("params")
        if not model_params:
            return None

        learning_rate = float(params.get("learning_rate", 0.01))
        batch_size = int(params.get("batch_size", 32))
        sample_num = int(params.get("sample_num", batch_size))

    module_name = "neursafe_fl.python.libs.optimizer.%s.%s" % (
        get_runtime().lower(), SCAFFOLD)

    module = __import__(module_name, fromlist=True)
    class_name = "Scaffold"
    if params:
        return getattr(module, class_name).get_instance(
            model_params=model_params, lr=learning_rate,
            batch_size=batch_size, sample_num=sample_num)

    return getattr(module, class_name).get_instance()


def get_optimizer_single_ins(name):
    """Get the single instance of optimizer.
    """
    if name.lower() == SCAFFOLD:
        return _create_scaffold(params=None)

    raise NotImplementedError("Not support single instance for "
                              "optimizer %s" % name)


def _parse_params():
    optimizer_params = os.getenv(TASK_OPTIMIZER_PARAM)
    params = {}
    if optimizer_params:
        for item in optimizer_params.split(","):
            key, value = item.split("::")
            params[key] = value
    return params


def create_optimizer(**kwargs):
    """Create optimizer for train script.
    """
    optimizer_name = os.getenv(TASK_OPTIMIZER)
    optimizer_params = _parse_params()
    optimizers = {"fedprox": _create_fedprox,
                  "scaffold": _create_scaffold}

    if optimizer_name not in optimizers:
        logging.warning("Not found optimizer %s", optimizer_name)
        return None

    optimizer_params.update(kwargs)
    return optimizers[optimizer_name](optimizer_params)
