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

# Storage
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "posix")
WORKSPACE = os.getenv("WORKSPACE", "/workspace")

# Temporary dir name in WORKSPACE
TEMP_DIR = os.getenv("TEMP_DIR", "tmp")

# S3 Storage
S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
WORKSPACE_BUCKET = os.getenv("WORKSPACE_BUCKET")

# POSIX Storage
WORKSPACE_PVC = os.getenv("WORKSPACE_PVC")

# System environment
SELECTOR_ADDRESS = os.getenv("SELECTOR_ADDRESS")
HTTP_PORT = int(os.getenv("HTTP_PORT", "8080"))

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


REQUIRED_ENV_VARIABLES = ["DB_ADDRESS", "DB_USERNAME", "DB_PASSWORD", "DB_TYPE",
                          "DB_NAME", "DB_COLLECTION_NAME", "HTTP_PORT",
                          "SELECTOR_ADDRESS", "JOB_SCHEDULER_ADDRESS",
                          "MODEL_MANAGER_ADDRESS", "K8S_ADDRESS",
                          "TEMP_DIR", "COORDINATOR_IMAGE", "PROXY_ADDRESS"]

# Proxy config(Refer to neursafe_fl/python/trans/proxy.py)
# Infrastructure config(Refer to neursafe_fl/python/libs/cloud/const.py)
