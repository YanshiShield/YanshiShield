#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Util functions definition
"""

import sys
import time
from absl import logging

import neursafe_fl.python.resource_manager.const as const
from neursafe_fl.python.resource_manager.errors import RetryError
from neursafe_fl.python.libs.db.errors import DataBaseError
from neursafe_fl.python.resource_manager.plat_form.errors import PlatformError


def _retry(func, error_list, *args, **kwargs):
    retry_time = 0
    while retry_time <= const.MAX_RETRY_TIMES:
        try:
            return func(*args, **kwargs)
        except error_list as error:
            logging.exception(str(error))
            retry_time += 1
            time.sleep(const.RETRY_INTERVAL)

    raise RetryError()


def _exit_abnormally(err_msg):
    """
    Program exit abnormally and log out error message.
    """
    logging.error("Program exit abnormally: %s", err_msg)
    sys.exit(1)


def db_operation_retry(func):
    """
    func wrapper

    when db connect failed, retry to connect db. If retry times beyond max retry
    times, program exit.

    Args:
        func: which func to be executed.
    """

    def wrapper(*args, **kwargs):
        try:
            return _retry(func, DataBaseError,
                          *args, **kwargs)
        except RetryError:
            err_msg = "Connect Database error, resource manager exit."
            _exit_abnormally(err_msg)

    return wrapper


def platform_operation_retry(func):
    """
    func wrapper

    when platform connect failed, retry to connect. If retry times beyond max
    retry times, program exit.

    Args:
        func: which func to be executed.
    """

    def wrapper(*args, **kwargs):
        try:
            return _retry(func, PlatformError,
                          *args, **kwargs)
        except RetryError:
            err_msg = "Platform connect error, resource manager exit."
            _exit_abnormally(err_msg)

    return wrapper
