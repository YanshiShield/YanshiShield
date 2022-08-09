#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
# pylint:disable=too-few-public-methods
"""Parse task config.
"""

import asyncio
import json
import os

from neursafe_fl.python.client.validation import raise_exception


MAX_TRY_TIME = 3
WAIT_SECOND = 0.5


def assert_task_config(config_file, config, task_type):
    """Assert task config is valid. if invalid, raise exception.

    Args:
        config_file: The asserted config file name.
        config: The asserted config.
        task_type: Train or evaluate task.
    """
    def assert_task_type():
        if (task_type not in config
                or not isinstance(config[task_type], dict)):
            raise_exception('Task type is invalidation, task config file: %s. '
                            'Please check' % config_file)
    assert_task_type()

    def assert_task_spec(task_spec):
        def is_item_exist(item):
            return item in task_spec and task_spec[item]

        def assert_correct_type(item, expect_type):
            if not isinstance(task_spec[item], expect_type):
                raise_exception('%s configure in config file is invalidate. '
                                'expect type is %s' % (item, expect_type))

        def assert_required(item):
            if item not in task_spec or not task_spec[item]:
                raise_exception('%s is required. Please check config file %s. '
                                % (item, config_file))

        if is_item_exist('timeout'):
            assert_correct_type('timeout', int)

        assert_required('command')
        assert_required('entry')

        if not is_item_exist('params'):
            task_spec['params'] = {}

        assert_correct_type('params', dict)

    assert_task_spec(config[task_type])


class TaskConfigParser:
    """It is used to parse the entry config of a task,
    and check whether the config is valid.
    """

    def __init__(self, task_spec, workspace, task_config_entry):
        """
        Args:
            task_spec: Task specification from the server.
            workspace: The working path of the client, saves some
                temporary files, including task specification from the server.
            task_config_entry: A path local to the client that saves the entry
                configuration of a series of tasks.
        """
        if task_spec.entry_name:
            self.__root = task_config_entry
            self.__entry_file = os.path.join(
                self.__root, task_spec.entry_name + '.json')
        else:
            self.__root = os.path.join(workspace, task_spec.scripts.path)
            self.__entry_file = os.path.join(
                self.__root, task_spec.scripts.config_file)

    async def parse(self, task_type):
        """Get config based on config file name, and assert config valid.

        Args:
            task_type: Training or evaluation task.
        """
        json_config = await self.__wait_read_success()
        config = json.loads(json_config)
        if 'script_path' not in config:
            config['script_path'] = self.__root
        assert_task_config(self.__entry_file, config, task_type)

        return config

    async def __wait_read_success(self):
        try_time = 0
        while try_time < MAX_TRY_TIME:
            try_time += 1
            try:
                with open(self.__entry_file, 'r') as cfg_file:
                    value = cfg_file.read()
                    if value == "":
                        # The decompressed data to minio cannot be read
                        # immediately, it should wait a short time and
                        # then read it.
                        await asyncio.sleep(WAIT_SECOND)
                    else:
                        return value
            except FileNotFoundError:
                raise_exception(
                    'The task %s configure file not exist.' % self.__entry_file)
        raise_exception(
            'The task %s configure file is empty.' % self.__entry_file)
