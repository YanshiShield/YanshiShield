#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
environment variable config
"""

import os

# Federated job
SUPPORTED_SECURE_ALGORITHM = ["DP", "SSA"]
SUPPORTED_RUNTIME = ["TENSORFLOW", "PYTORCH"]

# Database config
DB_TYPE = os.getenv("DB_TYPE", "mongo")
DB_ADDRESS = os.getenv("DB_ADDRESS")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "federated_learning")
DB_COLLECTION_NAME = os.getenv("DB_COLLECTION_NAME", "jobs")

# System environment
SELECTOR_ADDRESS = os.getenv("SELECTOR_ADDRESS")
HTTP_PORT = int(os.getenv("HTTP_PORT", "8080"))
SOURCE_MOUNT_PATH = os.getenv("SOURCE_MOUNT_PATH", "/mnt/minio")

# Mount SOURCE_MOUNT_PATH into WORKSPACE PATH in Pod
WORKSPACE = os.getenv("WORKSPACE", "/workspace")

# Temporary dir name in WORKSPACE
TEMP_DIR = os.getenv("TEMP_DIR", "tmp")

# Coordinator config
COORDINATOR_IMAGE = os.getenv("COORDINATOR_IMAGE", "fl-coordinator:latest")
COORDINATOR_WORKSPACE_PATH = os.getenv("COORDINATOR_WORKSPACE_PATH", "/fl")
DEPLOYMENT_WAY = os.getenv("DEPLOYMENT_WAY", "cloud")
COORDINATOR_PORT = os.getenv("COORDINATOR_PORT", "50051")

# coordinator environment variable
REPORT_PERIOD = os.getenv("REPORT_PERIOD", "10")
JOB_SCHEDULER_ADDRESS = os.getenv("JOB_SCHEDULER_ADDRESS", "job-scheduler:8088")
MODEL_MANAGER_ADDRESS = os.getenv("MODEL_MANAGER_ADDRESS",
                                  "fl-model-manager:50057")

# system internal const variable
DEFAULT_CLIENT_NUM = int(os.getenv("DEFAULT_CLIENT_NUM", "1"))
RESOURCE_CHECK_MAX_TIMES = int(os.getenv("RESOURCE_CHECK_MAX_TIMES", "600"))
COORDINATOR_HEARTBEAT_TIMEOUT = int(
    os.getenv("COORDINATOR_HEARTBEAT_TIMEOUT", "20"))
MAX_RETRY_TIMES = int(os.getenv("MAX_RETRY_TIMES", "30"))
RETRY_INTERVAL = int(
    os.getenv("COORDINATOR_QUERY_INTERVAL", "1"))


REQUIRED_ENV_VARIABLES = ["DB_ADDRESS", "DB_USERNAME", "DB_PASSWORD",
                          "HOST_ROOT_PATH", "JS_DIR_NAME_IN_HOST", "K8S_ADDRESS"
                          "COORDINATOR_IMAGE", "JOB_SCHEDULER_ADDRESS",
                          "MODEL_MANAGER_ADDRESS", "PROXY_ADDRESS"]

# Proxy config(Refer to neursafe_fl/python/trans/proxy.py)
# Infrastructure config(Refer to neursafe_fl/python/libs/cloud/const.py)
