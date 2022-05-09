#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=unused-argument, broad-except
"""Extender Module.
"""
import os
import sys
import importlib
from types import FunctionType
from absl import logging


def load(config):
    """Load a function from config or http webhook.
    {
        "mode": "http | file"
        "path": ""
        "url": ""
        "method_name": ""
    }
    """
    try:
        if config.get("mode") == "http":
            return web_request(config["url"], config["method_name"])

        if config.get("mode") == "file":
            return file_func(config["path"], config["method_name"])

        logging.warning("Not support extender mode %s", config)
    except Exception as err:
        logging.warning("Load extender failed, %s", str(err))
    return None


def file_func(path, func_name):
    """Load function from local file.
    """
    if not path or not os.path.exists(path) or not func_name:
        logging.warning("No extender path: %s or function: %s are loaded.",
                        path, func_name)
        return None

    env_path, module_name = os.path.split(path)
    if env_path not in sys.path:
        sys.path.append(env_path)

    module = importlib.import_module(module_name.rstrip(".py"))
    extender_func = getattr(module, func_name)
    logging.info("Load extender function: %s success.", func_name)
    return extender_func


def web_request(url, request):
    """Make a web hook request to outside service.
    """


def filter_extender(context, clients):
    """Extender Interface, Filter clients, abandon not matched clients.

    Args:
        context: extender function or http request to execute.
        clients: list of client, client is dict format.
    Returns:
        A list of client that being filtered.
    """
    try:
        if isinstance(context, FunctionType):
            return context(clients)
        return _call_webhook(context, clients)
    except Exception as err:
        logging.warning("Extender %s execute failed, %s", context, str(err))
        return clients  # won't affect default filtered clients


def score_extender(context, client):
    """Extender Interface, Score the client according client's info.

    Args:
        context: extender function or http request to execute.
        client: client info with dict format.
    """
    try:
        if isinstance(context, FunctionType):
            result = context(client)
        else:
            result = _call_webhook(context, client)
        return int(result)

    except Exception as err:
        logging.warning("Extender %s execute failed, %s", context, str(err))
        return 0


def _call_webhook(request, body):
    """Call request through http(s).
    """
    raise NotImplementedError
