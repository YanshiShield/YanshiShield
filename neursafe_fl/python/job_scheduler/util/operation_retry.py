#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
operation retry

when operation failed, it will retry, after retry max times, it will execute
callback function.for example, if db write failed, then retry write max times,
but if write still failed, program exit abnormally.
"""

import time
from absl import logging

from tornado import gen

import neursafe_fl.python.job_scheduler.util.const as const
import neursafe_fl.python.job_scheduler.util.errors as errors
from neursafe_fl.python.trans.proxy import ProxyError
from neursafe_fl.python.libs.db.errors import DataBaseError
from neursafe_fl.python.job_scheduler.util.abnormal_exit import exit_abnormally


@gen.coroutine
def __async_retry(func, error_list, *args, **kwargs):
    retry_time = 0
    while retry_time <= const.MAX_RETRY_TIMES:
        try:
            res = yield func(*args, **kwargs)
            raise gen.Return(res)
        except error_list as error:
            logging.exception(str(error))
            retry_time += 1
            yield gen.sleep(const.RETRY_INTERVAL)

    raise errors.RetryError()


def __retry(func, error_list, *args, **kwargs):
    retry_time = 0
    while retry_time <= const.MAX_RETRY_TIMES:
        try:
            return func(*args, **kwargs)
        except error_list as error:
            logging.exception(str(error))
            retry_time += 1
            time.sleep(const.RETRY_INTERVAL)

    raise errors.RetryError()


def coordinator_operation_retry(func):
    """
    func wrapper

    when coordinator create, get status and delete failed, retry these
    operations. If retry times beyond max retry times, program exit.

    Args:
        func: which func to be executed.
    """
    @gen.coroutine
    def wrapper(*args, **kwargs):
        try:
            res = yield __async_retry(func, (errors.CoordinatorCreateFailed,
                                             errors.CoordinatorDeleteFailed,
                                             errors.CoordinatorGetFailed),
                                      *args, **kwargs)
            raise gen.Return(res)
        except errors.RetryError:
            err_msg = "coordinator operation error, job scheduler exit."
            exit_abnormally(err_msg)

    return wrapper


def route_operation_retry(func):
    """
    func wrapper

    when route create and delete failed, retry these operations. If retry times
    beyond max retry times, program exit.

    Args:
        func: which func to be executed.
    """
    @gen.coroutine
    def wrapper(*args, **kwargs):
        try:
            res = yield __async_retry(func, ProxyError,
                                      *args, **kwargs)
            raise gen.Return(res)
        except errors.RetryError:
            err_msg = "proxy register operation error, job scheduler exit."
            exit_abnormally(err_msg)

    return wrapper


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
            return __retry(func, DataBaseError,
                           *args, **kwargs)
        except errors.RetryError:
            err_msg = "Connect Database error, job scheduler exit."
            exit_abnormally(err_msg)

    return wrapper
