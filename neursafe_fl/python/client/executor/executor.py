#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Task executor.
"""
import os
import abc

DEFAULT_TASK_TIMEOUT = 180


def create_executor(platform, **kwargs):
    """Create a platform's executor.

    Args:
        platform: The platform the executor runs on, its value is linux or k8s.
        kwargs: The parameters to create executor.

    Return:
        Return a specified executor based on platform.
    """
    model_name = 'neursafe_fl.python.client.executor.%s_executor' \
                 % platform.lower()
    model = __import__(model_name, fromlist=True)
    class_name = '%sExecutor' % platform.capitalize()
    return getattr(model, class_name)(**kwargs)


class Executor:  # pylint:disable=too-many-instance-attributes
    """The base executor, used to execute task on different platform.

    Args:
        task_id: Task ID.
        task_info: Task info from server.
        run_config: Contain task run command, parameters and others.
        cwd_path: The Path where is the executor's current work directory.
        workspace: The working path of the task will save the temporary
            information generated during training or evaluation, such as
            the initial weight and the weight after training, etc.
    """

    def __init__(self, **kwargs):
        self._id = kwargs['id_']
        self._executor_info = kwargs['executor_info']
        self._run_config = kwargs['run_config']
        self._cwd = kwargs['cwd']
        self._workspace = kwargs['workspace']
        self._datasets = kwargs.get('datasets')
        self._resource_spec = kwargs['resource_spec']
        self._distributed_env = kwargs['distributed_env']
        self._basic_envs = kwargs.get("basic_envs", {})

        self._timer = None

    def _gen_pythonpath(self):
        python_path = os.getenv('PYTHONPATH', '')
        if self._cwd in python_path.split(':'):
            return python_path
        return '%s:%s' % (python_path, self._cwd)

    @abc.abstractmethod
    async def execute(self):
        """Execute task.

        Run task on different platform. such as, create subprocess to execute
        task on linux, and create pod on kubernete platform.
        """

    @abc.abstractmethod
    async def delete(self):
        """Delete executor.
        """

    @abc.abstractmethod
    async def status(self):
        """return executor status.
        """
