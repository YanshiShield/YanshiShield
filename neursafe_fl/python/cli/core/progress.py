#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-few-public-methods
"""Show progress.
"""
import os
import sys
import time
import shutil
import threading


_1KB = 1024
_1MB = 1024 * 1024
_1GB = 1024 * 1024 * 1024


class ProgressPercentage:
    """Help show progress in upload  and download file."""
    def __init__(self, filename, callback=None, **kwargs):
        self._filename = filename
        if kwargs.get("download"):
            self._size = float(kwargs.get("size"))
        else:
            self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._start_time = time.time()
        self._pre_time = self._start_time
        self._lock = threading.Lock()
        self._callback = callback

    def __call__(self, bytes_amount):
        with self._lock:
            self._seen_so_far += bytes_amount
            now = time.time()

            ready_size = self.__cal_ready_size()
            speed = self.__cal_speed(now, bytes_amount)

            percentage = "{:.2f}%".format(self._seen_so_far / self._size * 100)
            upload_time = time.strftime("%M:%S",
                                        time.localtime(now - self._start_time))

            terminal_size = shutil.get_terminal_size()
            max_filename_size = terminal_size.columns - 44
            if max_filename_size < 0:
                max_filename_size = 0
            holder_filename = self.__gen_filename_placeholder(
                max_filename_size)

            format_str = "\r{0:<" + str(max_filename_size) + \
                "} {1:<8s} {2:<10s} {3:<12s} {4:<10s}"
            sys.stdout.write(
                format_str.format(holder_filename, percentage, ready_size,
                                  speed, upload_time))
            sys.stdout.flush()

            if self._callback:
                self._callback(bytes_amount)

    def __cal_speed(self, now, bytes_amount):
        speed = bytes_amount / (now - self._pre_time)
        if speed < _1KB:
            speed = "{:.2f}B/s".format(speed)
        elif speed < _1MB:
            speed = "{:.2f}KB/s".format(speed / _1KB)
        elif speed < _1GB:
            speed = "{:.2f}MB/s".format(speed / _1MB)
        else:
            speed = "{:.2f}GB/s".format(speed / _1GB)
        self._pre_time = now
        return speed

    def __cal_ready_size(self):
        ready_size = self._seen_so_far
        if ready_size < _1KB:
            ready_size = "{:.2f}B".format(ready_size)
        elif ready_size < _1MB:
            ready_size = "{:.2f}KB".format(ready_size / _1KB)
        elif ready_size < _1GB:
            ready_size = "{:.2f}MB".format(ready_size / _1MB)
        else:
            ready_size = "{:.2f}GB".format(ready_size / _1GB)
        return ready_size

    def __gen_filename_placeholder(self, max_filename_size):
        base_name = os.path.basename(self._filename)
        if len(base_name) < max_filename_size:
            return base_name
        return base_name[:max_filename_size]
