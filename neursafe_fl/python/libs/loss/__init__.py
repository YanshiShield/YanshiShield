#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Loss init.
"""

import os


def _get_optimizer_path():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "optimizer")


loss_config = {
    "tensorflow_feddc": {
        "script_path": os.path.join(_get_optimizer_path(), "tensorflow"),
        "entry": "scaffold_compute.py",
        "broadcast": "broadcast_control_variates",
        "aggregate": "aggregate_control_variates",
        "finish": "save_control_variates"
    },
    "pytorch_feddc": {
        "script_path": os.path.join(_get_optimizer_path(), "pytorch"),
        "entry": "scaffold_compute.py",
        "broadcast": "broadcast_control_variates",
        "aggregate": "aggregate_control_variates",
        "finish": "save_control_variates"
    }
}
