#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""FL SDK const.
"""

import os

TASK_WORKSPACE = "TASK_WORKSPACE"
TASK_RUNTIME = "TASK_RUNTIME"
DATASETS = "DATASETS"


def get_task_workspace():
    """Get task workspace from env.

    When start task, the client will set TASK_WORKSPACE to env.
    """
    return os.getenv(TASK_WORKSPACE)


def get_runtime():
    """Get runtime from env.

    When start task, the client will set TASK_RUNTIME to env.
    """
    return os.getenv(TASK_RUNTIME)


def get_datasets():
    """Get datasets from env.

    When start task, the client will set DATASETS to env.
    """
    return os.getenv(DATASETS)
