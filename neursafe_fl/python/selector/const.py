#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Const and Environments of client selector.
"""
import os

# Storage
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "posix")

# S3 Storage
S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
WORKSPACE_BUCKET = os.getenv("WORKSPACE_BUCKET")

WORKSPACE = os.getenv("WORKSPACE", "/workspace")
