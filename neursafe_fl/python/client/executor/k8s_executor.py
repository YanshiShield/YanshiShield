#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-few-public-methods
"""
Kubernetes executor, task will execute on kubernetes cluster.
"""
import asyncio
from absl import logging

from neursafe_fl.python.client.executor.executor import Executor
from neursafe_fl.python.libs.cloud.task import K8sTask, TaskExisted, \
    TaskCreateFailed, TaskNotExist, TaskDeleteFailed, TaskGetFailed
from neursafe_fl.python.sdk.utils import TASK_RUNTIME, TASK_WORKSPACE, DATASETS
import neursafe_fl.python.client.const as const
from neursafe_fl.python.client.executor.errors import FLError
from neursafe_fl.python.utils.file_io import read_json_file
from neursafe_fl.python.client.worker import WorkerStatus
from neursafe_fl.python.libs.cloud.const import K8S_NAMESPACE


WAIT_INTERVAL = 1


class K8sExecutor(Executor):
    """K8s Executor

    Manage task execution lifecycle and task will run in pod.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.__k8s_client = K8sTask()

    async def execute(self):
        """Execute task and wait it finished.

        In k8s, it will create pods to run task, and wait pods
        finished.
        """
        await self.__create_pod()

    async def __create_pod(self):
        node_id = self._resource_spec["node_id"]
        resource = self._resource_spec["resource"]
        cmds = self.__construct_cmd()
        volumes = [("workspace", self._workspace, self._workspace),
                   ("cwd", self._cwd, self._cwd),
                   ("datasets", self._datasets, self._datasets)]
        self.__add_dataset_volume(volumes)
        envs = self.__set_env_vars()

        try:
            await self.__k8s_client.create(name=self._id,
                                           namespace=K8S_NAMESPACE,
                                           cmds=cmds,
                                           image=const.CONTAINER_EXECUTOR_IMAGE,
                                           volumes=volumes,
                                           envs=envs,
                                           port=const.WORKER_PORT,
                                           node_id=node_id,
                                           resources=resource,
                                           working_dir=self._cwd)
        except TaskExisted as err:
            logging.warning(str(err))
            await self.__delete_pod()
            await self.__wait_pod_deleted()
            await self.__create_pod()
        except TaskCreateFailed as err:
            logging.exception(str(err))
            raise FLError(str(err)) from err

    async def __delete_pod(self):
        try:
            await self.__k8s_client.delete(name=self._id,
                                           namespace=K8S_NAMESPACE)
        except TaskNotExist:
            logging.info("Pod: %s not existing, no need to delete.",
                         self._id)
        except TaskDeleteFailed as err:
            logging.exception(str(err))
            raise FLError(str(err)) from err

    async def __wait_pod_deleted(self):
        while True:
            try:
                task = await self.__k8s_client.get(self._id,
                                                   namespace=K8S_NAMESPACE)
                status = task['state'].upper()
                logging.debug("Pod: %s status: %s",
                              self._id, status)
            except TaskNotExist:
                logging.info("Pod: %s deleted.",
                             self._id)
                break
            except TaskGetFailed as err:
                logging.exception(str(err))

            await asyncio.sleep(WAIT_INTERVAL)

    async def delete(self):
        """delete worker
        """
        await self.__delete_pod()

    async def status(self):
        try:
            task = await self.__k8s_client.get(self._id,
                                               namespace=K8S_NAMESPACE)
            status = task['state'].upper()
            logging.debug("Pod: %s status: %s",
                          self._id, status)
            return status
        except TaskNotExist:
            logging.info("Pod: %s deleted.",
                         self._id)
            return WorkerStatus.DELETED
        except TaskGetFailed as err:
            logging.exception(str(err))
            return None

    def __construct_cmd(self):
        cmds = []

        params = dict(self._run_config['params'],
                      **self._executor_info.spec.params)

        args = [self._run_config['entry']]
        for key, value in params.items():
            args.append('%s' % key)
            if value:
                args.append(value)

        cmds.append(self._run_config['command'])
        cmds.extend(args)
        return cmds

    def __set_env_vars(self):
        env_vars = {
            TASK_RUNTIME: self._executor_info.spec.runtime,
            TASK_WORKSPACE: self._workspace,
            'PYTHONPATH': self._gen_pythonpath(),
            'OPTIMIZER_NAME': self._executor_info.spec.optimizer.name
        }
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

        if const.WORKER_HTTP_PROXY:
            env_vars["http_proxy"] = const.WORKER_HTTP_PROXY

        if const.WORKER_HTTPS_PROXY:
            env_vars["https_proxy"] = const.WORKER_HTTPS_PROXY

        if const.WORKER_HTTP_PROXY or const.WORKER_HTTPS_PROXY:
            env_vars["no_proxy"] = self._id

        if len(self._resource_spec) > 1:
            for key, value in self._distributed_env.items():
                env_vars[key] = value

        return env_vars

    def __add_dataset_volume(self, volumes):
        datasets = read_json_file(self._datasets)
        used_datasets = self._executor_info.spec.datasets
        if used_datasets:
            for index, used_dataset in enumerate(used_datasets.split(",")):
                if datasets.get(used_dataset, None):
                    volumes.append(("dataset-" + str(index),
                                    datasets[used_dataset],
                                    datasets[used_dataset]))
                else:
                    logging.warning("Not exist %s in datasets, %s.",
                                    used_dataset, self._datasets)
