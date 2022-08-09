#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-few-public-methods
"""
Platform generator factory
"""
from neursafe_fl.python.resource_manager.plat_form.kubernetes import Kubernetes
from neursafe_fl.python.resource_manager.plat_form.standalone import Standalone


class PlatFormType:
    """Platform type
    """
    K8S = "k8s"
    STANDALONE = "linux"


def gen_platform(platform_name, event_callbacks):
    """Generate specific platform object

    According to deployment, generate specific platform object

    Args:
        platform_name: k8s or linux
        event_callbacks: watch event callback functions

    Returns:
        platform: specific platform
    """
    platforms = {PlatFormType.K8S: Kubernetes,
                 PlatFormType.STANDALONE: Standalone}

    return platforms[platform_name](event_callbacks)
