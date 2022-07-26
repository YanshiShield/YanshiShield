#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
const variable
"""

import os

DB_ADDRESS = os.getenv("DB_ADDRESS")
DB_TYPE = os.getenv("DB_TYPE", "mongo")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

DB_NAME = os.getenv("DB_NAME", "fl_tasks")
DB_COLLECTION_NAME = os.getenv("DB_COLLECTION_NAME", "tasks")

MAX_RETRY_TIMES = int(os.getenv("MAX_RETRY_TIMES", "30"))
RETRY_INTERVAL = int(
    os.getenv("COORDINATOR_QUERY_INTERVAL", "1"))

GPU_RS_KEY = os.getenv("GPU_RS_KEY", "nvidia.com/gpu")

CLUSTER_LABEL_KEY = os.getenv("CLUSTER_LABEL_KEY", "kubernetes.io/cluster_id")
CLUSTER_LABEL_VALUE = os.getenv("CLUSTER_LABEL_VALUE")
