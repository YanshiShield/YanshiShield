#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
const environment definition
"""

import os

CONTAINER_EXECUTOR_IMAGE = os.getenv("CONTAINER_EXECUTOR_IMAGE")

WORKER_PORT = int(os.getenv("WORKER_PORT", "8050"))
WAIT_WORKER_FINISHED_TIMEOUT = int(os.getenv("WAIT_WORKER_FINISHED_TIMEOUT",
                                             "300"))
WORKER_HTTP_PROXY = os.getenv("WORKER_HTTP_PROXY")
WORKER_HTTPS_PROXY = os.getenv("WORKER_HTTPS_PROXY")
