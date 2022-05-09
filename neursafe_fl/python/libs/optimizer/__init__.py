#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Module init."""

import os


optimizer_config = {
    "tensorflow_scaffold": {
        "script_path": os.path.join(os.path.dirname(__file__), "tensorflow"),
        "entry": "scaffold_compute.py",
        "broadcast": "broadcast_control_variates",
        "aggregate": "aggregate_control_variates",
        "finish": "save_control_variates"
    },
    "pytorch_scaffold": {
        "script_path": os.path.join(os.path.dirname(__file__), "pytorch"),
        "entry": "scaffold_compute.py",
        "broadcast": "broadcast_control_variates",
        "aggregate": "aggregate_control_variates",
        "finish": "save_control_variates"
    }
}
