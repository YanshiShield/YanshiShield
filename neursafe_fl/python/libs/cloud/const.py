#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
Const variables definition
"""

import os


CLOUD_OS = os.getenv('CLOUD_OS', 'k8s')
K8S_ADDR = os.getenv('K8S_ADDRESS', "0.0.0.0")
K8S_API_PROTOCOL = os.getenv('K8S_API_PROTOCOL', 'http')
K8S_API_TOKEN = os.getenv('K8S_API_TOKEN', '')
K8S_NAMESPACE = os.getenv("K8S_NAMESPACE", "default")

GPU_RS_KEY = os.getenv("GPU_RS_KEY", "nvidia.com/gpu")
