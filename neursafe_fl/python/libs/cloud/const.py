#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
Const variables definition
"""

import os


CLOUD_OS = os.getenv("CLOUD_OS", "k8s")
K8S_ADDR = os.getenv("K8S_ADDRESS", "0.0.0.0:6443")
K8S_API_PROTOCOL = os.getenv("K8S_API_PROTOCOL", "https")
K8S_API_TOKEN = os.getenv("K8S_API_TOKEN", "some_token_string")
K8S_NAMESPACE = os.getenv("K8S_NAMESPACE", "default")

K8S_IMAGE_PULL_SECRETS = os.getenv("K8S_IMAGE_PULL_SECRETS", None)
GPU_RS_KEY = os.getenv("GPU_RS_KEY", "nvidia.com/gpu")
