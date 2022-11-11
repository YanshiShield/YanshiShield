#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Coordinator configuration validation."""

import re

from neursafe_fl.python.utils.file_io import read_json_file
from neursafe_fl.python.libs.secure.const import \
    SUPPORTED_SECURE_ALGORITHM, SecureAlgorithm
from neursafe_fl.python.libs.compression.quantization import \
    check_quantization_bits
from neursafe_fl.python.libs.compression.subsampling import check_sampling_rate
from neursafe_fl.python.libs.compression.const import \
    CompressionAlgorithm, SUPPORTED_COMPRESSION_ALGORITHM


DEFAULT_HYPER_CONFIG = {
    "max_round_num": 10,
    "client_num": 1,
    "threshold_client_num": 1,
    "round_timeout": 3600,
    "evaluate_interval": 2,
    "save_interval": 5,
    "learning_rate": 1.0
}


def validate_config(config):
    """Validate user configuration."""
    if config.get('config_file'):
        new_config = read_json_file(config["config_file"])
        config.update(new_config)

    new_config = _set_default_value(config)
    _validate_params(new_config)
    _validate_task_entry(new_config)
    return new_config


def _set_default_value(config):
    if config.get("hyper_parameters"):
        DEFAULT_HYPER_CONFIG.update(config["hyper_parameters"])

    config["hyper_parameters"] = DEFAULT_HYPER_CONFIG
    return config


def _validate_task_entry(config):
    is_entry_valid = ("task_entry" in config
                      and config["task_entry"] is not None)
    is_scripts_valid = "scripts" in config and config["scripts"] is not None
    if is_entry_valid == is_scripts_valid:
        raise ValueError(("Required key: one of 'task_entry' and 'scripts'. "
                         "Got %s.") % str(config))

    if is_entry_valid:
        _validate_required({"task_entry": str}, config)
    if is_scripts_valid:
        _validate_required({"path": str, "config_file": str},
                           config["scripts"])


def _validate_params(config):
    """Validate federate job configuration.

    Args:
        config: configuration to be validated.
    """
    _validate_basic_params(config)
    _validate_hyper_params(config["hyper_parameters"])

    if "secure_algorithm" in config and "compression" in config:
        raise ValueError("Not support secure algorithm with compression.")

    if "secure_algorithm" in config:
        _validate_secure_algorithm(config["secure_algorithm"])

        if (config["secure_algorithm"]["type"].upper()
                == SUPPORTED_SECURE_ALGORITHM[1]):
            __set_and_validate_ssa_config(
                config["secure_algorithm"],
                config["hyper_parameters"]['client_num'],
                config["hyper_parameters"]['threshold_client_num'])

    if "compression" in config:
        _validate_compression_algorithm(config["compression"])


def _validate_basic_params(config):
    required_rules = {"job_name": str,
                      "description": str,
                      "host": str,
                      "port": int,
                      "model_path": str,
                      "runtime": str,
                      "hyper_parameters": dict}
    optional_rules = {"ssl": str,
                      "clients": str,
                      "parameters": dict,
                      "extenders": dict,
                      "resource": dict,
                      "secure_algorithm": dict,
                      "datasets": str}
    _validate_required(required_rules, config)
    _validate_optional(optional_rules, config)

    regular_fields = {
        "job_name": r'[a-z0-9]([-a-z0-9]{0,98}[a-z0-9])?$',
        'host': r'\b((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.|$)){4}\b'
    }
    _validate_regular(regular_fields, config)


def _validate_hyper_params(config):
    optional_rules = {"max_round_num": int,
                      "client_num": int,
                      "threshold_client_num": int,
                      "round_timeout": int,
                      "evaluate_interval": int,
                      "save_interval": int,
                      "learning_rate": float}
    _validate_optional(optional_rules, config)


def __validate_quantization_algorithm(config):
    required_rules = {"quantization_bits": int}
    _validate_required(required_rules, config)

    check_quantization_bits(config["quantization_bits"])


def __validate_subsampling_algorithm(config):
    required_rules = {"sampling_rate": float}
    _validate_required(required_rules, config)

    check_sampling_rate(config["sampling_rate"])


def _validate_compression_algorithm(config):
    required_rules = {"type": str}
    _validate_required(required_rules, config)

    if config["type"].upper() not in SUPPORTED_COMPRESSION_ALGORITHM:
        raise ValueError("Compression algorithm: %s is not supported, support "
                         "algorithm is %s" % (config["type"],
                                              SUPPORTED_COMPRESSION_ALGORITHM))

    if config["type"].upper() == CompressionAlgorithm.quantization.value:
        __validate_quantization_algorithm(config)

    if config["type"].upper() == CompressionAlgorithm.subsampling.value:
        __validate_subsampling_algorithm(config)


def _validate_secure_algorithm(config):
    required_rules = {"type": str}

    _validate_required(required_rules, config)

    if config["type"].upper() not in SUPPORTED_SECURE_ALGORITHM:
        raise ValueError("Secure algorithm: %s is not supported, support "
                         "algorithm is %s" % (config["type"],
                                              SUPPORTED_SECURE_ALGORITHM))

    if config["type"].upper() == SecureAlgorithm.dp.value:
        __validate_secure_algorithm_with_dp(config)
    elif config["type"].upper() == SecureAlgorithm.ssa.value:
        __validate_secure_algorithm_with_ssa(config)


def __validate_secure_algorithm_with_dp(config):
    required_rules = {"type": str,
                      "noise_multiplier": float}
    optional_rules = {"adding_same_noise": bool}

    _validate_required(required_rules, config)
    _validate_optional(optional_rules, config)


def __validate_secure_algorithm_with_ssa(config):
    required_rules = {"type": str}
    optional_rules = {"threshold": int,
                      "mode": str,
                      "use_same_mask": bool}

    _validate_required(required_rules, config)
    _validate_optional(optional_rules, config)

    __set_and_validate_mode_with_ssa(config)


def __set_and_validate_mode_with_ssa(config):
    if "mode" not in config:
        config["mode"] = "doublemask"

    if config["mode"].lower() not in ("onemask", "doublemask"):
        raise ValueError("Mode for SSA must be in (onemask, doublemask), "
                         "recommend onemask used in cross-silo, "
                         "doublemask used in cross-device.")

    if "use_same_mask" not in config:
        config["use_same_mask"] = False


def __set_and_validate_ssa_config(config, client_num, threshold_client_num):
    if threshold_client_num < client_num / 2:
        raise ValueError("Threshold_client_num in hyper_parameters must be "
                         "larger than half client_num when use ssa, this will "
                         "be more secure")

    if "threshold" not in config:
        config["threshold"] = threshold_client_num

    if config["threshold"] < client_num / 2:
        raise ValueError("Threshold in SSA config must be larger than"
                         " half client_num when use ssa, this will "
                         "be more secure")

    if config["threshold"] < 2:
        raise ValueError("Threshold in SSA config must >= 2, now setted %s"
                         % config["threshold"])
    if config["threshold"] > threshold_client_num:
        raise ValueError("Threshold in SSA config must <= "
                         "threshold_client_num in hyper_parameters")


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
            _assert_match_regular(config[key], pattern)


def _assert_match_regular(context, pattern):
    """Validate whether the context match the regular expression.

    Args:
        context: the string to be verified.
        pattern: Regular expression to be satisfied.
    """
    valid = re.compile(pattern)
    result = valid.match(context)
    if result is None:
        raise ValueError("%s not satisfied with pattern: %s" %
                         (context, pattern))
