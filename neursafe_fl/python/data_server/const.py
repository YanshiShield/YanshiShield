#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Const and Environments of data server.
"""

import os

SERVER_ADDRESS = os.getenv("SERVER_ADDRESS", "0.0.0.0")
PORT = int(os.getenv("PORT", "30088"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()

# ------storage environments------
WORKSPACE = os.getenv("WORKSPACE", "/workspace")

# Storage
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "posix")

# S3 Storage
S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
WORKSPACE_BUCKET = os.getenv("WORKSPACE_BUCKET")

# data server authentication
ACCESS_USER = os.getenv("ACCESS_USER", "nsfl")
ACCESS_PASSWORD = os.getenv("ACCESS_PASSWORD", "1qaz@WSX#EDC")
