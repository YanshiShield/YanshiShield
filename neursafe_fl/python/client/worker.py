#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-few-public-methods, invalid-name,
# pylint:disable=too-many-arguments, too-many-instance-attributes
"""
Worker definition. Split fl task to some workers, workers will do task
execution. Worker will chose specific executor to finish task.
"""
import pickle

import neursafe_fl.python.sdk.utils as utils

from neursafe_fl.python.client.executor.executor import create_executor
from neursafe_fl.python.libs.secure.secure_aggregate.ssa_client import \
    gen_secret_file_path


class WorkerStatus:
    """worker statue
    """
    FAILED = "FAILED"
    COMPLETED = "SUCCEEDED"
    RUNNING = "RUNNING"
    DELETED = "DELETED"


class Worker:
    """
    Worker class definition.
    """

    def __init__(self, id_, type_, client_config, worker_info,
                 worker_config, workspace, distributed_env, resource_spec,
                 grpc_metadata):
        self.id = id_
        self.type = type_
        self._client_config = client_config
        self._worker_info = worker_info
        self._worker_config = worker_config
        self._workspace = workspace
        self._distributed_env = distributed_env
        self._resource_spec = resource_spec
        self._grpc_metadata = grpc_metadata

        self._executor = None

    async def execute(self):
        """
        Execute worker
        """
        self._executor = create_executor(
            self._client_config['platform'],
            id_=self.id,
            executor_info=self._worker_info,
            run_config=self._worker_config[self.type],
            cwd=self._worker_config['script_path'],
            workspace=self._workspace,
            datasets=self._client_config.get('datasets'),
            resource_spec=self._resource_spec,
            distributed_env=self._distributed_env,
            basic_envs=self._gen_basic_envs()
        )

        await self._executor.execute()

    def _gen_basic_envs(self):
        env_vars = {
            utils.WORKER_ID: self.id,
            utils.ROUND_NUM: str(self._worker_info.metadata.round),
            utils.TASK_RUNTIME: self._worker_info.spec.runtime,
            utils.TASK_WORKSPACE: self._workspace,
            utils.TASK_OPTIMIZER: self._worker_info.spec.optimizer.name,
            utils.TASK_LOSS: self._worker_info.spec.loss.name,
            utils.GRPC_METADATA: str(pickle.dumps(self._grpc_metadata)),
            utils.CERTIFICATION_PATH: self._client_config.get("ssl", ""),
            utils.SECURITY_ALGORITHM: str(pickle.dumps(
                self._worker_info.spec.secure_algorithm)),
            utils.SERVER_ADDRESS: self._client_config["server"],
            utils.TASK_METADATA: str(pickle.dumps(self._worker_info.metadata)),
            utils.TASK_TIMEOUT: str(
                self._worker_config[self.type].get("timeout")),
            utils.SSA_SECRET_PATH: gen_secret_file_path(self._workspace)
        }

        if self._worker_info.spec.optimizer.params:
            env_vars[utils.TASK_OPTIMIZER_PARAM] = self._gen_str_params(
                self._worker_info.spec.optimizer.params)

        return env_vars

    def _gen_str_params(self, params):
        params_list = []
        for key in params:
            params_list.append("%s::%s" % (key, params[key]))
        return ",".join(params_list)

    async def delete(self):
        """
        Delete worker
        """
        if self._executor:
            await self._executor.delete()

    async def status(self):
        """
        Return worker status
        """
        if self._executor:
            return await self._executor.status()

        raise WorkerStatus.DELETED
