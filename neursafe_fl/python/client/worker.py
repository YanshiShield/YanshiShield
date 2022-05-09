#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-few-public-methods, invalid-name,
# pylint:disable=too-many-arguments, too-many-instance-attributes
"""
Worker definition. Split fl task to some workers, workers will do task
execution. Worker will chose specific executor to finish task.
"""
from neursafe_fl.python.client.executor.executor import create_executor


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
                 worker_config, workspace, distributed_env, resource_spec):
        self.id = id_
        self.type = type_
        self._client_config = client_config
        self._worker_info = worker_info
        self._worker_config = worker_config
        self._workspace = workspace
        self._distributed_env = distributed_env
        self._resource_spec = resource_spec

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
            distributed_env=self._distributed_env)

        await self._executor.execute()

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
