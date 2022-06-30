#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Const and Environments of model manager.
"""

import os


HTTP_PORT = os.getenv("PORT", "50057")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
HEARTBEAT_TIMEOUT = int(os.getenv("HEARTBEAT_TIMEOUT", "10"))
RETRY_TIMEOUT = int(os.getenv("RETRY_TIMEOUT", "10"))
RETRY_TIMES = int(os.getenv("RETRY_TIMES", "3"))
DB_RETRY_INTERVAL = int(os.getenv("DB_RETRY_INTERVAL", "1"))

# ------database environments------
DB_TYPE = os.getenv("DB_TYPE")
DB_ADDRESS = os.getenv("DB_ADDRESS")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

DB_NAME = os.getenv("DB_NAME", "federated_learning")
DB_COLLECTION_NAME = os.getenv("DB_COLLECTION_NAME", "models")

# ------storage environments------
WORKSPACE = os.getenv("WORKSPACE", "/workspace")
MODELS_DIR = os.getenv("MODELS_DIR", "models")

STORAGE_TYPE = os.getenv("STORAGE_TYPE", "posix")
STORAGE_ENDPOINT = os.getenv("STORAGE_ENDPOINT")
STORAGE_ACCESS_KEY = os.getenv("ACCESS_KEY")
STORAGE_SECRET_KEY = os.getenv("SECRET_KEY")
