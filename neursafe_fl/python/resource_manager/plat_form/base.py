#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
Platform base class

Different deployment type means different platform, such as: stand alone, k8s
and so on.
"""

import abc


class Platform:
    """Platform base class
    """

    def __init__(self, event_callbacks):
        self._event_callbacks = event_callbacks

    @abc.abstractmethod
    def fetch_nodes(self):
        """Return all nodes

        Returns:
            nodes: nodes info
        """

    @abc.abstractmethod
    def watch_nodes(self):
        """Watch nodes

        Watch node event and handle this event, such as: node add, node modify,
        node delete. Watch should be executed in thread or in async type.
        """
