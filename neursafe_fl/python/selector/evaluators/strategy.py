#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Strategy Module.
"""

import importlib
from absl import logging


DefaultStrategy = {
    "resource": 1,
    "data": 1
}


def load_strategy(config):
    """Load all the evaluator based on config.

    Strategy is composed with a few evaluators, config with dict format, such
    as:
        Key: evaluator_name     Value: weight_value
        {
            "resource": 1,
            "data": 1
        }
    The Strategy will use every evaluator in the config to score the client,
    then add up all the scores, which as the final score of client.
    """
    strategy = {}
    if not config:
        # set default strategy
        config = DefaultStrategy

    for key in config:
        weight = int(config[key])
        evaluator = _load_evaluator(key, weight)
        if evaluator:
            strategy[key] = evaluator

    return strategy


def _load_evaluator(evaluator_name, weight):
    try:
        module_name = "neursafe_fl.python.selector.evaluators.%s_eval" % evaluator_name
        module = importlib.import_module(module_name)
        evaluator_class = getattr(module,
                                  "%sEvaluator" % evaluator_name.capitalize())
        evaluator = evaluator_class(weight)
        logging.info("Load evaluator: %s success.", evaluator_name)
        return evaluator
    except ImportError as err:
        logging.warning("Load evaluator: %s failed, reason: %s",
                        evaluator_name, str(err))
        return None
