#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=unused-argument
"""Scaffold computation in server.
"""

import os
import numpy as np

S = 1
N = 1

parent_path = os.path.dirname(os.path.abspath(__file__))
Init_GLOBAL_C_PATH = "%s/init_global_variates.npy" % parent_path
AGGREGATE_GLOBAL_C_PATH = "/tmp/global_variates.npy"


def multiply(variable, constant):
    """multiply of list with constant
    """
    if isinstance(variable, list):
        return [val * constant for val in variable]
    return variable * constant


def aggregate_control_variates(data, previous):
    """aggregate all clients' local variates to global control variates
    """
    if previous:
        control_variates = previous.get("control_variates", 0)
        total_weight = previous.get("total_weight", 0)
    else:
        control_variates = 0
        total_weight = 0

    weight = 1
    if "sample_num" in list(data["metrics"].keys()):
        weight = data["metrics"]["sample_num"]

    for file in os.listdir(data["custom_files"]):
        if file == "delta_control_variates.npy":
            file_path = os.path.join(data["custom_files"], file)
            local_c = np.load(file_path, allow_pickle=True)
            if isinstance(control_variates, int) and control_variates == 0:
                control_variates = multiply(local_c, weight)
            else:
                control_variates = np.add(control_variates,
                                          multiply(local_c, weight))

    return {"control_variates": control_variates,
            "total_weight": total_weight + weight}


def broadcast_control_variates(params):  # pylint:disable=unused-argument
    """add global control variates file to params, broadcast to client.
    """
    # send with params or file
    custom_files = {}
    if os.path.exists(Init_GLOBAL_C_PATH):
        custom_files = {"global_variates.npy": Init_GLOBAL_C_PATH}
    custom_params = {}

    # find last round aggregated control_variates
    if os.path.exists(AGGREGATE_GLOBAL_C_PATH):
        custom_files["global_variates.npy"] = AGGREGATE_GLOBAL_C_PATH

    return custom_files, custom_params


def save_control_variates(params, aggregated_weights=None):
    """Save the server control variates to file, for next round."""
    # decay_lr = global_lr * max(0.1, pow(0.5, round_num))
    aggregated_c = params.get("control_variates", 0)
    total_weight = params.get("total_weight", 1)
    average_c = np.true_divide(aggregated_c, total_weight)

    old_server_c = 0
    if os.path.exists(AGGREGATE_GLOBAL_C_PATH):
        old_server_c = np.load(AGGREGATE_GLOBAL_C_PATH, allow_pickle=True)

    new_server_c = np.add(old_server_c, multiply(average_c, (S / N)))
    np.save(AGGREGATE_GLOBAL_C_PATH, new_server_c)
    return {"global_variates.npy": AGGREGATE_GLOBAL_C_PATH}
