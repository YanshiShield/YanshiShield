#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Validation of model parameters
"""

import re


def validate_config(config):
    """Validate the legality of the parameters in config.
    """
    required_rules = {"namespace": str,
                      "name": str,
                      "runtime": str}
    optional_rules = {"description": str,
                      "version": str,
                      "model_path": str}

    _validate_required(required_rules, config)
    _validate_optional(optional_rules, config)
    regular_fields = {
        "name": r'([\w|\-]{0,100})',
        'version': r'([\w|\-]{0,100})'
    }
    _validate_regular(regular_fields, config)


def _validate_required(rules, config):
    """Validate required parameters in config.

    Config must contains every field that in rules, and the same data type.

    Args:
        rules: rules is a dict contains field and data type requirements.
        config: config to be validated.
    """
    for key in rules:
        if key not in config:
            raise ValueError("Required key: '%s' not exist" % key)
        if not isinstance(config[key], rules[key]):
            raise TypeError("Expect '%s' type: %s, but got: %s" %
                            (key, rules[key], type(config[key])))


def _validate_optional(rules, config):
    """Validate optional parameters in config.

    Config may contain field that defined in rules, if contains, must has the
    same data type.

    Args:
        rules: rules is a dict contains field and data type requirements.
        config: config to be validated.
    """
    for key in rules:
        if key in config:
            if config[key] and not isinstance(config[key], rules[key]):
                raise TypeError("Expect '%s' type: %s, but got: %s" %
                                (key, rules[key], type(config[key])))


def _validate_regular(patterns, config):
    for key, pattern in patterns.items():
        if key in config:
            valid = re.compile(pattern)
            result = valid.match(config[key])
            if result is None:
                raise ValueError("%s not satisfied with pattern: %s" %
                                 (config[key], pattern))
