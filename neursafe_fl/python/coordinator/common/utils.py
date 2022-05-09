#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Define some tool functions."""

import os
import sys
import shutil
import importlib
from types import FunctionType

from absl import logging

from neursafe_fl.python.runtime.runtime_factory import Runtime


def runtime_suffix(runtime):
    """Mapping the suffix of the different runtime's file."""
    suffix_map = {Runtime.TENSORFLOW.value: '.h5',
                  Runtime.PYTORCH.value: '.pth'}
    if runtime in suffix_map.keys():
        return suffix_map[runtime]
    return ""


def join(path, *paths):
    """Merge paths.

    Args:
        path: root of the path
        paths: list of sub paths
    """
    sub_path = "/"
    for item in paths:
        sub_path = os.path.join(sub_path, item.lstrip("/"))
    return os.path.join(path, sub_path.lstrip("/"))


def delete(path):
    """Delete file or directory."""
    shutil.rmtree(path)


def load_module(script_path, func_name):
    """Load third-party modules.

    Args:
        script_path: the file path of the modules
        func_name: the function name need to be loaded
    Returns:
        loaded module
    """
    if not script_path or not os.path.exists(script_path) or not func_name:
        logging.warning("No extender script: %s or function: %s are loaded.",
                        script_path, func_name)
        return None

    # add module python path
    env_path, module_name = os.path.split(script_path)
    if env_path not in sys.path:
        sys.path.append(env_path)

    try:
        module = importlib.import_module(module_name.rstrip(".py"))
        extender_func = getattr(module, func_name)
        if not isinstance(extender_func, FunctionType):
            raise TypeError("not a function")
        logging.info("Load extender function: %s success.", func_name)
        return extender_func
    except Exception as err:  # pylint:disable=broad-except
        logging.warning("Load extender function: %s failed, reason: %s",
                        func_name, str(err))
        return None
