#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-few-public-methods
"""Const for selector component."""
import os


class ClientType:
    """Support device type.
    """
    Single = "single"
    Cluster = "cluster"


class State:
    """Client report status.
    """
    Idle = "idle"
    Full = "full"  # the client is occupied
    Available = "available"  # the client is idle
    Error = "error"  # the client is error


class HeartBeat:
    """Heartbeat interval, unit second.
    """
    Single = int(os.getenv("SINGLE_HEART", "300"))
    Cluster = int(os.getenv("CLUSTER_HEART", "600"))

    @staticmethod
    def min_time():
        """Return the minimum time interval.
        """
        client_type_time = [HeartBeat.Single, HeartBeat.Cluster]
        return min(client_type_time)

    @staticmethod
    def get(client_type):
        """Return the time interval according the client type.
        """
        interval_map = {ClientType.Single: HeartBeat.Single,
                        ClientType.Cluster: HeartBeat.Cluster}
        return interval_map.get(client_type, 100)
