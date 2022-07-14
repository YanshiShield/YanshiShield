#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Validate client initial config.
"""

import os
import re

from absl import logging

from neursafe_fl.python.utils.file_io import list_all_files


class ParameterError(Exception):
    """Parameter error.
    """


REQUIRED_CONFIG_ITEM = ('server', 'lmdb_path', 'workspace',
                        'platform', 'task_config_entry')


def _get_support_platform():
    executor_path = os.path.join(os.path.dirname(__file__), 'executor')
    files = list_all_files(executor_path)

    support_platform = []
    match_rule = re.compile(r'(?P<platform>[\w_]*)_executor.py$')
    for filename in files:
        result = match_rule.match(filename)
        if result:
            support_platform.append(result.group('platform'))
    return support_platform


SUPPORT_PLATFORM = _get_support_platform()


def validate_agent_config(config):
    """Validate client agent configure. Raise the exception when configure
    is invalidate.

    Args:
        config: The client agent's config.
    """
    def assert_required(item_key):
        # TODO: should complete help command.
        if item_key not in config or not config[item_key]:
            raise_exception('The configure of %s is required, '
                            'please run --help for help.'
                            % item_key)
    # Check the required configure items are exist.
    for item in REQUIRED_CONFIG_ITEM:
        assert_required(item)

    def assert_path_exist(item_key):
        if not os.path.exists(config[item_key]):
            raise_exception("%s's path not exist." % item_key)

    # Assert the required paths in configure are exist.
    for item in ('workspace', 'task_config_entry'):
        assert_path_exist(item)

    if "datasets" in config:
        assert_path_exist("datasets")

    if config['platform'].lower() not in SUPPORT_PLATFORM:
        raise_exception('Platform must be in %s.' % SUPPORT_PLATFORM)

    def validate_resource_config(resource):
        if resource:
            _assert_resource_item('cpu', resource.get('cpu', 0), min_value=0)
            _assert_resource_item('memory', resource.get('memory', 0),
                                  min_value=0)
            _assert_resource_item('gpu', resource.get('gpu', 0), min_value=0)

    validate_resource_config(config.get('resource', None))

    if config['storage_quota'] <= 0:
        raise_exception('Storage quota: %s must be larger than 0.'
                        % config['storage_quota'])


def validate_task_info(request):
    """Assert task info from server. Raise exception when task info is
    invalidate.

    Args:
        request: This is a request info from server, contain task info.
    """
    # if not set job name, the value is ""
    __validate_job_name(request.metadata.job_name)
    __validate_round_num(request.metadata.round)

    __validate_task_entry(request.spec)
    if not request.spec.runtime:
        raise_exception('Runtime is required')

    __validate_parameters(request.spec.params)
    __validate_parameters(request.spec.custom_params)
    __validate_parameters(request.spec.secure_algorithm)

    __validate_resource(request.spec.resource)


def __validate_task_entry(config):
    is_entry_effective = (config.HasField("entry_name")
                          and config.entry_name is not None)
    is_scripts_effective = (config.HasField("scripts")
                            and config.scripts is not None)
    if not is_entry_effective ^ is_scripts_effective:
        raise ValueError(("Required key: one of 'entry_name' and 'scripts'. "
                         "Got %s.") % str(config))

    if is_entry_effective and not isinstance(config.entry_name, str):
        raise_exception('Config_file must be string.')
    if (is_scripts_effective
            and not isinstance(config.scripts.config_file, str)
            and not isinstance(config.scripts.path, str)):
        raise_exception(
            'Values(scripts.config_file, scripts.path) must be str.')


def __validate_parameters(parameters):
    for _, value in parameters.items():
        if value is None:
            continue
        if not isinstance(value, (int, float, bool, str)):
            raise_exception(
                'Parameter value only support int/float/str/bool, '
                'the value:%s not supported.' % value)


def __validate_resource(resource):
    _assert_resource_item('cpu', resource.cpu, min_value=0.0)
    _assert_resource_item('memory', resource.memory, min_value=0)
    _assert_resource_item('gpu', resource.gpu, min_value=0)
    _assert_resource_item('worker_num', resource.worker_num, min_value=1)

    if not resource.cpu and not resource.memory and not resource.gpu:
        raise_exception("Cpu, gpu, memory all are 0, no resource request.")


def __validate_job_name(job_name):
    """validate job name
    """
    if not job_name:
        raise_exception('Job name is required')

    valid = re.compile(r'[a-z0-9]([-a-z0-9]{0,98}[a-z0-9])?$')

    result = valid.match(job_name)
    if result is None:
        raise_exception('Job name:%s is invalid, '
                        'must be [a-z0-9]([-a-z0-9]{0,98}[a-z0-9])?$.'
                        % job_name)


def __validate_round_num(round_num):
    """validate round num
    """
    if not (isinstance(round_num, int) and round_num >= 0):
        raise_exception('The round num must be >= 0.')


def _assert_resource_item(name, value, min_value=None, max_value=None):
    if min_value and value < min_value:
        raise_exception('The %s resource configure is invalidate, '
                        'should great than %s' % (name, min_value))

    if max_value and value > max_value:
        raise_exception('The %s resource configure is invalidate,'
                        'should less than %s' % (name, max_value))


def raise_exception(err_msg):
    """Raise exception.
    """
    logging.error(err_msg)
    raise ParameterError(err_msg)
