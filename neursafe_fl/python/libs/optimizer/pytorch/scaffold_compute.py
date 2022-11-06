#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=no-member, invalid-name, too-many-arguments, unused-argument
"""Scaffold computation in server.
"""
import os
import torch

S = 1
N = 1

parent_path = os.path.dirname(os.path.abspath(__file__))
Init_GLOBAL_C_PATH = "%s/init_global_variates.pt" % parent_path
AGGREGATE_GLOBAL_C_PATH = "/tmp/global_variates.pt"


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
        if file == "delta_control_variates.pt":
            file_path = os.path.join(data["custom_files"], file)
            local_c = torch.load(file_path, map_location=torch.device("cpu"))

            if control_variates == 0:
                control_variates = []
                for p in local_c:
                    control_variates.append(torch.multiply(p, weight))
            else:
                sum_variates = []
                for c, p in zip(control_variates, local_c):
                    sum_variates.append(torch.add(c, torch.multiply(p, weight)))
                control_variates = sum_variates

    return {"control_variates": control_variates,
            "total_weight": total_weight + weight}


def broadcast_control_variates(params):  # pylint:disable=unused-argument
    """add global control variates file to params, broadcast to client.
    """
    # send with params or file
    custom_files = {}
    if os.path.exists(Init_GLOBAL_C_PATH):
        custom_files = {"global_variates.pt": Init_GLOBAL_C_PATH}
    custom_params = {}

    # find last round aggregated control_variates
    if os.path.exists(AGGREGATE_GLOBAL_C_PATH):
        custom_files["global_variates.pt"] = AGGREGATE_GLOBAL_C_PATH

    return custom_files, custom_params


def save_control_variates(params, aggregated_weights=None):
    """Save the server control variates to file, for next round."""
    # decay_lr = global_lr * max(0.1, pow(0.5, round_num))
    aggregated_c = params.get("control_variates", 0)
    total_weight = params.get("total_weight", 1)
    if aggregated_c:
        # calculate average of aggregated control variates
        avg_server_c = []
        for agg_c in aggregated_c:
            avg_server_c.append(torch.true_divide(agg_c, total_weight))

        # load last round server control variates
        old_server_c = [torch.zeros_like(p.data) for p in aggregated_c]
        if os.path.exists(AGGREGATE_GLOBAL_C_PATH):
            old_server_c = torch.load(AGGREGATE_GLOBAL_C_PATH,
                                      map_location=torch.device("cpu"))

        # update the server control variates
        new_server_c = []
        for old_c, delta in zip(old_server_c, avg_server_c):
            tmp = torch.multiply(delta, (S / N))
            new_server_c.append(torch.add(old_c, tmp))

        torch.save(new_server_c, AGGREGATE_GLOBAL_C_PATH)
        return {"global_variates.pt": AGGREGATE_GLOBAL_C_PATH}

    return {}
