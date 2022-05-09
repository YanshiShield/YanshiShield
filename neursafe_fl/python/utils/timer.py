#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Async timer
"""

from asyncio import get_running_loop


class Timer:
    """Manage async timer.
    """

    def __init__(self, interval, callback):
        self.__interval = interval
        self.__callback = callback
        self.__handle = None

    def start(self, *args, **kwargs):
        """Start timer, the interval is seconds.
        """
        loop = get_running_loop()
        self.__handle = loop.call_later(
            self.__interval, self.__callback, *args, **kwargs)

    def cancel(self):
        """Cancel timer if timer started.
        """
        if self.__handle:
            self.__handle.cancel()
        self.__handle = None
