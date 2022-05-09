#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Coordinator configuration validation."""

import re
import os

import neursafe_fl.python.job_scheduler.util.const as const
from neursafe_fl.python.job_scheduler.job import State


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


def _validate_required_paras(rules, config, scope):
    """Validate required parameters in config.

    Config must contains every field that in rules, and the same data type.

    Args:
        rules: rules is a dict contains field and data type requirements.
        config: config to be validated.
        scope: config belongs to which scope

    Raises:
        TypeError: value is not expected type.
        ValueError: value is not correct.
    """
    for key in rules:
        if key not in config:
            raise ValueError(
                "Required key: '%s' not exist in %s" % (key, scope))
        if not isinstance(config[key], rules[key]):
            raise TypeError("Expect '%s' type: %s, but got: %s in %s" %
                            (key, rules[key], type(config[key]), scope))


def _validate_optional_paras(rules, config, scope):
    """Validate optional parameters in config.

    Config may contain field that defined in rules, if contains, must has the
    same data type.

    Args:
        rules: rules is a dict contains field and data type requirements.
        config: config to be validated.
        scope: config belongs to which scope

    Raises:
        TypeError: value is not expected type.
    """
    for key in rules:
        if key in config:
            if not isinstance(config[key], rules[key]):
                raise TypeError("Expect '%s' type: %s, but got: %s in %s" %
                                (key, rules[key], type(config[key]), scope))


def _validate_mutex_paras(rules, config, scope):
    """Validate mutex parameters in config.

    Args:
        rules: rules is a dict contains field and data type requirements.
        config: config to be validated.
        scope: config belongs to which scope

    Raises:
        TypeError: value is not expected type.
        ValueError: value is not correct.
    """
    if not set(rules.keys()) & set(config.keys()):
        raise ValueError(
            'Mutex parameters: %s must exist one.' % (list(rules.keys())))

    for key in rules:
        if key in config:
            if not isinstance(config[key], rules[key]):
                raise TypeError("Expect '%s' type: %s, but got: %s in %s" %
                                (key, rules[key], type(config[key]), scope))


def _validate_resource(config):
    optional_rules = {"worker_num": int,
                      "gpu": int,
                      "memory": int,
                      "cpu": float}

    _validate_optional_paras(optional_rules, config, "resource")

    def assert_param_effective(param_value, param_name):
        if param_value < 0:
            raise ValueError(
                "Param %s: %s not effective, should greater than 0."
                % (param_name, param_value))

    for key, value in config.items():
        assert_param_effective(value, key)


def _validate_hyper_parameters(config):
    optional_rules = {"max_round_num": int,
                      "client_num": int,
                      "threshold_client_num": int,
                      "round_timeout": int,
                      "evaluate_interval": int,
                      "save_interval": int,
                      "learning_rate": float}

    _validate_optional_paras(optional_rules, config, "hyper_parameters")

    def assert_param_effective(param_name, param_value):
        if param_value <= 0:
            raise ValueError(
                "Param %s: %s not effective, should greater than 0."
                % (param_name, param_value))

    for key, value in config.items():
        assert_param_effective(key, value)

    if config.get("threshold_client_num", 1) > config.get("client_num", 1):
        raise ValueError("threshold_client_num must less than or equal "
                         "client_num in hyper_parameters")


def _validate_parameters(config):  # pylint: disable=unused-argument
    # TODO
    pass


def _validate_extenders(config):  # pylint: disable=unused-argument
    # TODO
    pass


def _validate_scripts(scripts):
    required_rules = {"path": str,
                      "config_file": str}

    _validate_required_paras(required_rules, scripts, "scripts")


def _validate_dp_algorithm(dp_algorithm):
    required_rules = {"type": str,
                      "noise_multiplier": float}
    optional_rules = {"adding_same_noise": bool}

    _validate_required_paras(required_rules, dp_algorithm, "secure_algorithm")
    _validate_optional_paras(optional_rules, dp_algorithm, "secure_algorithm")


def _validate_ssa_algorithm(config):
    required_rules = {"type": str}
    optional_rules = {"threshold": int,
                      "mode": str,
                      "use_same_mask": bool}

    _validate_required_paras(required_rules, config, "secure_algorithm")
    _validate_optional_paras(optional_rules, config, "secure_algorithm")

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

    if config["mode"].lower() == "onemask" and (
        config["threshold"] != client_num
            or threshold_client_num != client_num):
        raise ValueError("When use onemask, threshold in SSA config must == "
                         "threshold_client_num and client_num "
                         "in hyper_parameters")


def _validate_secure_algorithm(config):
    required_rules = {"type": str}

    _validate_required_paras(required_rules, config, "secure_algorithm")

    if config["type"].upper() not in const.SUPPORTED_SECURE_ALGORITHM:
        raise ValueError("Secure algorithm: %s is not supported, support "
                         "algorithm is %s."
                         % (config["type"], const.SUPPORTED_SECURE_ALGORITHM))

    if config["type"].upper() == "DP":
        _validate_dp_algorithm(config)
    elif config["type"].upper() == "SSA":
        _validate_ssa_algorithm(config)


def _validate_port(port):
    if port < 1024 or port > 65535:
        raise ValueError("Port: %s must in range 1024~65535." % port)


def _validate_runtime(runtime):
    if runtime.upper() not in const.SUPPORTED_RUNTIME:
        raise ValueError(
            "Runtime: %s not in supported runtime: %s."
            % (runtime, const.SUPPORTED_RUNTIME))


def validate_job_config(config):
    """
    Validate fl job config

    Args:
        config: config to be validated.

    Raises:
        TypeError: value is not expected type.
        ValueError: value is not correct.
    """
    required_para_rules = {"id": str,
                           "runtime": str,
                           "output": str}

    optional_para_rules = {"description": str,
                           "port": int,
                           "clients": str,
                           "model_path": str,
                           "model_id": str,
                           "checkpoint_id": str,
                           "hyper_parameters": dict,
                           "ssl": str,
                           "parameters": dict,
                           "extenders": dict,
                           "secure_algorithm": dict,
                           "datasets": str,
                           "resource": dict}

    mutex_para_rules = {"task_entry": str,
                        "scripts": dict}

    model_rules = {"model_path": str,
                   "model_id": str,
                   "checkpoint_id": str}

    regular_rules = {
        "id": r'[a-z0-9]([-a-z0-9]{0,98}[a-z0-9])?$'
    }

    _validate_required_paras(required_para_rules, config, "job")
    _validate_optional_paras(optional_para_rules, config, "job")
    _validate_mutex_paras(mutex_para_rules, config, "job")
    _validate_mutex_paras(model_rules, config, "job")

    _validate_regular(regular_rules, config)
    _validate_runtime(config["runtime"])

    if "port" in config:
        _validate_port(config["port"])

    if "scripts" in config:
        _validate_scripts(config["scripts"])

    if "resource" in config:
        _validate_resource(config["resource"])

    if "hyper_parameters" in config:
        _validate_hyper_parameters(config["hyper_parameters"])

    if "parameters" in config:
        _validate_parameters(config["parameters"])

    if "extenders" in config:
        _validate_extenders(config["extenders"])

    if "secure_algorithm" in config:
        _validate_secure_algorithm(config["secure_algorithm"])

        if config["secure_algorithm"]["type"].upper() == "SSA":
            __set_and_validate_ssa_config(
                config["secure_algorithm"],
                config["hyper_parameters"]['client_num'],
                config["hyper_parameters"]['threshold_client_num'])


def _validate_progress(progress):
    if progress < 0 or progress > 100:
        raise ValueError("Progress: %s must in range 0~100." % progress)


def _validate_state(state):
    if state not in State.ALL_STATES:
        raise ValueError(
            'State: %s not in correct states: %s' % (state,
                                                     State.ALL_STATES))


def _validate_checkpoints(checkpoints):
    for ckpt in checkpoints.values():
        if "path" not in ckpt:
            raise ValueError("path not exist in checkpoint: %s" % ckpt)

        if not ckpt["path"]:
            raise ValueError("path is empty in checkpoint: %s" % ckpt)

        if "accuracy" not in ckpt:
            raise ValueError("accuracy not exist in checkpoint: %s" % ckpt)

        if not isinstance(ckpt["accuracy"], float):
            raise ValueError("accuracy is not float in checkpoint: %s" % ckpt)


def validate_heartbeat(heartbeat):
    """
    Validate heartbeat info

    Args:
        heartbeat: heartbeat to be validated.

    Raises:
        TypeError: value is not expected type.
        ValueError: value is not correct.
    """
    required_para_rules = {"id": str,
                           "namespace": str,
                           "state": str,
                           "progress": int}

    optional_para_rules = {"reason": str,
                           "checkpoints": dict}

    _validate_required_paras(required_para_rules, heartbeat, "heartbeat")
    _validate_optional_paras(optional_para_rules, heartbeat, "heartbeat")

    _validate_progress(heartbeat["progress"])
    _validate_state(heartbeat["state"])

    if "checkpoints" in heartbeat:
        _validate_checkpoints(heartbeat["checkpoints"])


def validate_required_env():
    """
    Validate required environment variable.
    """
    for variable in const.REQUIRED_ENV_VARIABLES:
        if os.getenv(variable) is None:
            raise Exception("Env: %s not configure" % variable)
