#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
config environment variable
"""

import os


REPORT_PERIOD = int(os.getenv("REPORT_PERIOD", "10"))
JOB_SCHEDULER_ADDRESS = os.getenv("JOB_SCHEDULER_ADDRESS")
CKPT_ROOT_PATH = os.getenv("CKPT_ROOT_PATH", "checkpoints")

# if deployment way is cloud, mount path should be same with js env variables
DEPLOYMENT_WAY = os.getenv("DEPLOYMENT_WAY", "cloud")
COORDINATOR_WORKSPACE_PATH = os.getenv("COORDINATOR_WORKSPACE_PATH", "/fl")

MAX_RETRY_TIMES = 3
RETRY_TIMEOUT = 5

# Storage
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "posix")

# S3 Storage
S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
WORKSPACE_BUCKET = os.getenv("WORKSPACE_BUCKET")
