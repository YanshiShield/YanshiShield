#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
# pylint:disable=not-callable
"""Feddc computation in server.
"""
import torch
import numpy as np

from neursafe_fl.python.libs.loss.feddc_util import save_h_i, \
    compute_avg_h, save_all_h_i


def save_h_parameter(data, previous):
    """Save feddc's h_i in result.
    """
    result = save_h_i(data, previous)
    return result


def mean_h_paramters(params, aggregated_weights):
    """Mean h_i, and add avg_h to weights for feddc.
    """
    avg_h = compute_avg_h(params)
    _add_avg_h_to_weights(aggregated_weights, avg_h)
    save_all_h_i(params["h_i_s"])


def _add_avg_h_to_weights(aggregated_weights, avg_h):
    idx = 0
    for name, delta_w in aggregated_weights["weights"].items():
        length = len(delta_w.reshape(-1))
        aggregated_weights["weights"][name].data = np.add(
            delta_w,
            torch.tensor(avg_h[idx:idx + length].reshape(delta_w.shape)))
        idx += length
