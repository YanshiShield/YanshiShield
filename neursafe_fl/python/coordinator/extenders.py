#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint: disable=broad-except, lost-exception
"""Extender are interfaces for external script or processes to insert into the
default federated workflow."""

from absl import logging

from neursafe_fl.python.coordinator.errors import ExtendExecutionFailed

support_extenders = ["broadcast", "aggregate", "finish"]


def broadcast_extender(func, params):
    """Broadcast user's custom files or data to client in each round.

    Args:
        func: function to process user's custom data and files.
        params: extender parameters.
    Returns:
        all the data including custom files and params.
    Raises:
        ExtendExecutionFailed, when extender function executed failed.
    """
    if not func:
        return {}
    custom = {}
    try:
        files, data = func(params)
        custom["files"] = files
        custom["params"] = data
        logging.info("Broadcast extend func: %s exec success.", func.__name__)
        return custom
    except Exception as err:
        logging.exception("Broadcast extend func: %s exec failed, reason: %s",
                          func.__name__, str(err))
        raise ExtendExecutionFailed from err


def aggregate_extender(func, updates, previous=None):
    """Aggregate client's upload updates after each round finished.

    Args:
        func: function to process client's updates, including custom data and
              files, weights and metrics.
        updates: the current one client updates, is a dict.
                 explain: {"weights": model weights,
                           "metrics": training metrics,
                           "custom_files": all the custom files,
                           "custom_params": all the custom params}
        previous: the previous clients' updates process results.
    Returns:
        all the data including custom files and params.
    Raises:
        ExtendExecutionFailed, when extender function executed failed.
    """
    if not func:
        return None
    try:
        aggregated_result = func(updates, previous)
        logging.info("Aggregate extend func: %s exec success.", func.__name__)
        return aggregated_result
    except Exception as err:
        logging.exception("Aggregate extend func: %s exec failed, reason: %s",
                          func.__name__, str(err))
        raise ExtendExecutionFailed from err


def finish_extender(func, params):
    """Process the aggregated result after all the client's updates.

    Mainly calculate the aggregated result of all updates.

    Args:
        func: function to process client's updates, including custom data and
              files, weights and metrics.
        params: the aggregated result from aggregate extender after received
                enough client's updates.
    Returns:
        the final result of custom files and params for this round.
    Raises:
        ExtendExecutionFailed, when extender function executed failed.
    """
    if not func:
        return None
    try:
        result = func(params)
        logging.info("Finish extend func: %s exec success.", func.__name__)
        return result
    except Exception as err:
        logging.exception("Finish extend func: %s exec failed, reason: %s",
                          func.__name__, str(err))
        raise ExtendExecutionFailed from err
