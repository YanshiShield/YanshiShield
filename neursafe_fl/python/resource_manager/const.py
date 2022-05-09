#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
const variable
"""

import os
import json

CFG_FILE_PATH = os.getenv("CFG_FILE_PATH")

DB_ADDRESS = os.getenv("DB_ADDRESS")
DB_TYPE = os.getenv("DB_TYPE", "mongo")
DB_USERNAME = None
DB_PASSWORD = None
PLATFORM = "linux"

if CFG_FILE_PATH:
    with open(CFG_FILE_PATH, "r") as file:
        CONFIG_INFO = json.load(file)
    DB_USERNAME = CONFIG_INFO.get("DB_USERNAME")
    DB_PASSWORD = CONFIG_INFO.get("DB_PASSWORD")
    PLATFORM = CONFIG_INFO.get("platform")

DB_NAME = os.getenv("DB_NAME", "fl_tasks")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "tasks")

MAX_RETRY_TIMES = int(os.getenv("MAX_RETRY_TIMES", "30"))
RETRY_INTERVAL = int(
    os.getenv("COORDINATOR_QUERY_INTERVAL", "1"))

GPU_RS_KEY = os.getenv("GPU_RS_KEY", "nvidia.com/gpu")

CLUSTER_LABEL_KEY = os.getenv("CLUSTER_LABEL_KEY", "kubernetes.io/cluster_id")
CLUSTER_LABEL_VALUE = os.getenv("CLUSTER_LABEL_VALUE")
