#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=
"""Feddc computation in server.
"""
import numpy as np

from neursafe_fl.python.libs.loss.feddc_util import save_h_i, \
    compute_avg_h, save_all_h_i
import neursafe_fl.python.libs.optimizer.tensorflow.scaffold_compute as scaffold


def process_parameter(data, previous):
    """Aggregate scaffold's control variates and save feddc's h_i.
    """
    result = scaffold.aggregate_control_variates(data, previous)
    save_h_i(data, previous, result)
    return result


def broadcast_paramters(params):
    """Broadcast scaffold's control variates.
    """
    return scaffold.broadcast_control_variates(params)


def save_paramters(params, aggregated_weights):
    """Save the server control variates to file for scaffold, and add avg_h to
    weights for feddc.
    """
    result = scaffold.save_control_variates(params)

    avg_h = compute_avg_h(params)
    _add_avg_h_to_weights(aggregated_weights, avg_h)
    save_all_h_i(params["h_i_s"])
    return result


def _add_avg_h_to_weights(aggregated_weights, avg_h):
    idx = 0
    for w_idx, delta_w in enumerate(aggregated_weights["weights"]):
        length = len(delta_w.reshape(-1))
        aggregated_weights[w_idx] = np.add(
            delta_w,
            avg_h[idx:idx + length].reshape(delta_w.shape))
        idx += length
