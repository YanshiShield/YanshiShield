#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""GRPC Pool.
"""

import time
from grpclib.client import Channel
from grpclib.config import Configuration

from neursafe_fl.python.trans.ssl_helper import SSLContext
from neursafe_fl.python.utils.timer import Timer


CLEAN_CHANNEL_INTERVAL = 7200
MONITOR_INTERVAL = 3600


class GRPCPool:
    """GRPC Poll.
    """
    def __init__(self):
        self.__channels = {}

        self.__timer = None
        self.__start_monitor()

    @classmethod
    def instance(cls, *args, **kwargs):
        """Get GRPC Poll instance.
        """
        if not hasattr(GRPCPool, "_instance"):
            GRPCPool._instance = GRPCPool(*args, **kwargs)
        return GRPCPool._instance

    def get_channel(self, address, certificate_path):
        """Get channel in GRPC pool.

        Args:
            address: the reomte server's address, such as host:port.
            certificate_path: the ssl path if use grpcs.
        """
        if address in self.__channels:
            self.__channels[address]["alive_time"] = time.time()
            return self.__channels[address]["channel"]

        host, port = address.split(':')
        config = Configuration(
            _keepalive_time=300,
            _keepalive_timeout=CLEAN_CHANNEL_INTERVAL
        )
        channel = Channel(host, int(port),
                          ssl=SSLContext.instance(certificate_path),
                          config=config)
        self.__channels[address] = {
            "alive_time": time.time(),
            "channel": channel
        }
        return channel

    def close_all(self):
        """Close timer and grpc_channel.
        """
        if self.__timer:
            self.__timer.cancel()

        for channel_obj in self.__channels.values():
            channel_obj["channel"].close()

    def __start_monitor(self):
        interval_time = time.time() + MONITOR_INTERVAL
        self.__timer = Timer(interval_time, self.__clean_channels)
        self.__timer.start()

    def __clean_channels(self):
        now = time.time()
        for key, channel_obj in list(self.__channels.items()):
            if now - channel_obj["alive_time"] > CLEAN_CHANNEL_INTERVAL:
                channel_obj["channel"].close()
                del self.__channels[key]

        self.__start_monitor()
