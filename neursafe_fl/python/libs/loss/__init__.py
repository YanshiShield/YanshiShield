#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Loss init.
"""

import os


loss_config = {
    "tensorflow_feddc": {
        "script_path": os.path.join(os.path.dirname(__file__), "tensorflow"),
        "entry": "feddc_compute.py",
        "broadcast": "broadcast_paramters",
        "aggregate": "process_parameter",
        "finish": "save_paramters"
    },
    "pytorch_feddc": {
        "script_path": os.path.join(os.path.dirname(__file__), "pytorch"),
        "entry": "feddc_compute.py",
        "broadcast": "broadcast_paramters",
        "aggregate": "process_parameter",
        "finish": "save_paramters"
    }
}
