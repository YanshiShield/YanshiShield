#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
Exception definition
"""


class KubeClientError(Exception):
    """Kube client exception
    """


class GetNodesError(KubeClientError):
    """Get nodes exception
    """


class WatchNodesError(KubeClientError):
    """Watch nodes exception
    """
