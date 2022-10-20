#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=invalid-name
"""Loss for client sdk.
"""
import os
from absl import logging
from neursafe_fl.python.sdk.utils import get_runtime, TASK_LOSS, \
    TASK_LOSS_PARAM

FEDDC = "feddc"


def _create_feddc(*args, **kwargs):
    parmas = [("sample_num", int), ("batch_size", int), ("lr", float),
              ("epoch", int), ("alpha", float),
              ("print_loss_per_forward", int), ("print_loss_per_call", int)]

    for key, type_ in parmas:
        if key in kwargs:
            kwargs[key] = type_(kwargs[key])

    model_name = "neursafe_fl.python.libs.loss.%s.%s" % (
        get_runtime().lower(), FEDDC)
    model = __import__(model_name, fromlist=True)
    class_name = "FeddcLoss"
    if "device" in kwargs:
        return getattr(model, class_name).get_instance(*args, **kwargs)

    return getattr(model, class_name).get_instance(*args, **kwargs)


def _parse_params():
    optimizer_params = os.getenv(TASK_LOSS_PARAM, None)
    params = {}
    if optimizer_params:
        for item in optimizer_params.split(","):
            key, value = item.split("::")
            params[key] = value
    return params


def create_loss(*args, **kwargs):
    """Create loss for train script.
    """
    loss_name = os.getenv(TASK_LOSS)
    loss_params = _parse_params()
    losses = {FEDDC: _create_feddc}

    if loss_name not in losses:
        logging.warning("Not found loss %s", loss_name)
        return None

    loss_params.update(kwargs)
    return losses[loss_name](*args, **loss_params)
