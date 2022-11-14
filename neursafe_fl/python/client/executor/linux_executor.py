#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""The linux executor.
"""

import asyncio
import os
import signal
import contextlib

from absl import logging

import neursafe_fl.python.client.executor.errors as err
from neursafe_fl.python.client.executor.executor import Executor, \
    DEFAULT_TASK_TIMEOUT
from neursafe_fl.python.client.workspace.log import FLLogger
from neursafe_fl.python.sdk.utils import DATASETS
from neursafe_fl.python.utils.timer import Timer
from neursafe_fl.python.client.executor.cgroup import Cgroup
from neursafe_fl.python.client.worker import WorkerStatus


_MINUTE2SECOND = 60


class LinuxExecutor(Executor):
    """Executor run on linux.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__proc = None
        self.__monitor_timer = Timer(self.__get_timeout_interval(),
                                     self.__monitor_timeout)
        self.__cgroup = Cgroup(self._id)

        self.__status = None

    def __get_timeout_interval(self):
        config_value = self._run_config.get('timeout', DEFAULT_TASK_TIMEOUT)
        return config_value * _MINUTE2SECOND

    async def __start_task_process(self):
        cmd, args = self.__construct_cmd()
        self.__set_env_vars()

        logging.info('Task %s, start command: %s %s',
                     self._id, cmd, args)
        self.__proc = await asyncio.create_subprocess_exec(
            cmd, *args,
            stderr=asyncio.subprocess.PIPE,
            cwd=self._cwd)

        self.__set_resource_limit()

    def __monitor_timeout(self):
        self.delete()
        self.__monitor_timer = None

    async def __log_error(self):
        fl_logger = FLLogger(self._workspace)

        stderr = await self.__proc.stderr.read()

        logging.error(stderr.decode())
        fl_logger.error(stderr)

        fl_logger.close()

    async def status(self):
        if not self.__proc:
            return WorkerStatus.DELETED

        async def return_code(proc_):
            with contextlib.suppress(asyncio.TimeoutError):
                await asyncio.wait_for(proc_.wait(), 1e-6)
            return proc_.returncode

        code_ = await return_code(self.__proc)

        if code_ == 0:
            return WorkerStatus.COMPLETED

        if code_:
            await self.__log_error()
            return WorkerStatus.FAILED

        if code_ is None:
            return WorkerStatus.RUNNING

    def __stop_monitor_timer(self):
        self.__monitor_timer.cancel()
        self.__monitor_timer = None

    def __do_finished(self):
        self.__cgroup.clear()

        if not self.__monitor_timer:
            raise err.TaskTimeoutError(
                'Task %s run timeout %s.' % (
                    self._id, self._run_config['timeout']))

        self.__stop_monitor_timer()
        if self.__proc.returncode:
            raise err.TaskRunError('Task %s execute error, exist code: %s' % (
                self._id, self.__proc.returncode))

        self.__proc = None

    async def execute(self):
        """Execute task and wait it finished.

        In linux, will create subprocess to run task, and wait subprocess
        finished.
        """
        await self.__start_task_process()
        self.__monitor_timer.start()

    async def delete(self):
        """Cancel executor and stop task.
        """
        status = await self.status()

        if status == WorkerStatus.RUNNING:
            os.kill(self.__proc.pid, signal.SIGKILL)
        self.__do_finished()

    def __construct_cmd(self):
        params = dict(self._run_config['params'],
                      **self._executor_info.spec.params)

        args = [self._run_config['entry']]
        for key, value in params.items():
            args.append('%s' % key)
            if value:
                if isinstance(value, (int, float)):
                    args.append(str(value))
                else:
                    args.append(value)

        return self._run_config['command'], args

    def __set_env_vars(self):
        env_vars = {
            'PYTHONPATH': self._gen_pythonpath(),
        }
        env_vars.update(self._basic_envs)

        if self._executor_info.spec.optimizer.params:
            params = []
            for key in self._executor_info.spec.optimizer.params:
                params.append("%s::%s" %
                              (key,
                               self._executor_info.spec.optimizer.params[key]))
            env = ",".join(params)
            env_vars["OPTIMIZER_PARAMS"] = env

        if self._datasets:
            env_vars[DATASETS] = self._datasets

        self.__set_visible_gpus(env_vars)
        os.environ.update(env_vars)

    def __set_visible_gpus(self, env_vars):
        resource = self._resource_spec["resource"]
        if resource['gpu']:
            gpus = ','.join(
                str(item) for item in resource['gpu'])
            logging.info("Task %s's gpus is  %s", self._id,
                         gpus)
            env_vars["CUDA_VISIBLE_DEVICES"] = gpus

    def __set_resource_limit(self):
        resource = self._resource_spec["resource"]
        try:
            if resource['cpu'] > 0:
                self.__cgroup.set_cpu_quota(self.__proc.pid,
                                            resource['cpu'])

            if resource['memory'] > 0:
                self.__cgroup.set_memory_quota(self.__proc.pid,
                                               resource['memory'])
        except OSError as error:
            logging.warning(str(error))
