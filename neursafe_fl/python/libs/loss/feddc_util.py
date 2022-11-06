#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Utils for FedDC.
"""
import pickle
import os
import numpy as np

AVG_H_FILE = "/tmp/nsfl_avg_h.file"


def save_h_i(data, previous, result):
    """Save one client's h_i.
    """
    # previous is none when the first client reporte in a round.
    if previous is None:
        if os.path.exists(AVG_H_FILE):
            result["h_i_s"] = load_all_h_i()
        else:
            result["h_i_s"] = {}
    else:
        result["h_i_s"] = previous["h_i_s"]

    for file in os.listdir(data["custom_files"]):
        if file == "h_i.npy":
            file_path = os.path.join(data["custom_files"], file)
            h_i = np.load(file_path)
            result["h_i_s"][data["client_id"]] = h_i


def compute_avg_h(params):
    """Compute for h_i average.
    """
    h_is_s = list(params["h_i_s"].values())
    if len(h_is_s) != 1:
        avg_h = np.mean(h_is_s, axis=0)
    else:
        avg_h = h_is_s[0]

    return avg_h


def save_all_h_i(avg_h):
    """Save all client's h_i in server.
    """
    with open(AVG_H_FILE, "wb") as file_w:
        pickle.dump(avg_h, file_w)


def load_all_h_i():
    """Load all h_i.
    """
    with open(AVG_H_FILE, "rb") as file_r:
        return pickle.load(file_r)
