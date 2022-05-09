#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
environment variable config
"""

import os

# federated job
SUPPORTED_SECURE_ALGORITHM = ["DP", "SSA"]
SUPPORTED_RUNTIME = ["TENSORFLOW", "PYTORCH"]

# system environment
DB_ADDRESS = os.getenv("DB_ADDRESS")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
SELECTOR_ADDRESS = os.getenv("SELECTOR_ADDRESS")
ROUTE_REGISTER_ADDRESS = os.getenv("ROUTE_REGISTER_ADDRESS")
CLOUD_OS = os.getenv("CLOUD_OS", "k8s")
K8S_ADDRESS = os.getenv("K8S_ADDRESS")
HTTP_PORT = int(os.getenv("HTTP_PORT", "8080"))
COORDINATOR_IMAGE = os.getenv("COORDINATOR_IMAGE", "fl-coordinator:latest")
COORDINATOR_WORKSPACE_PATH = os.getenv("COORDINATOR_WORKSPACE_PATH", "/fl")
HOST_STORAGE_PATH = os.getenv("HOST_PATH", "/mnt/minio")
STORAGE_PATH = os.getenv("STORAGE_PATH", "/storage")
JS_NAMESPACE = os.getenv("JS_NAMESPACE", "tmp")
DEPLOYMENT_WAY = os.getenv("DEPLOYMENT_WAY", "cloud")
DB_TYPE = os.getenv("DB_TYPE", "mongo")
DEFAULT_CLIENT_NUM = int(os.getenv("DEFAULT_CLIENT_NUM", "1"))
RESOURCE_CHECK_MAX_TIMES = int(os.getenv("RESOURCE_CHECK_MAX_TIMES", "600"))

# system internal const variable
COORDINATOR_HEARTBEAT_TIMEOUT = int(
    os.getenv("COORDINATOR_HEARTBEAT_TIMEOUT", "20"))
MAX_RETRY_TIMES = int(os.getenv("MAX_RETRY_TIMES", "30"))
RETRY_INTERVAL = int(
    os.getenv("COORDINATOR_QUERY_INTERVAL", "1"))
DB_NAME = os.getenv("DB_NAME", "federated_learning")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "jobs")

REQUIRED_ENV_VARIABLES = ["DB_ADDRESS", "SELECTOR_ADDRESS", "K8S_ADDRESS",
                          "CLOUD_OS", "COORDINATOR_IMAGE", "PROXY_ADDRESS",
                          "STORAGE_PATH"]

# coordinator environment variable
REPORT_PERIOD = os.getenv("REPORT_PERIOD", "10")
JOB_SCHEDULER_ADDRESS = os.getenv("JOB_SCHEDULER_ADDRESS", "job-scheduler:8088")
MODEL_MANAGER_ADDRESS = os.getenv("MODEL_MANAGER_ADDRESS",
                                  "fl-model-manager:50057")
