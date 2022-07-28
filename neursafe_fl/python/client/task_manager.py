#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-few-public-methods, broad-except
"""Task manager.
"""
import asyncio
import os
import time


from absl import logging
from neursafe_fl.python.utils.lmdb_util import LMDBUtil
from neursafe_fl.python.client.task import create_task, TaskType
from neursafe_fl.python.client.validation import ParameterError
from neursafe_fl.python.resource_manager.rm import ResourceManager

_RUNNING_TASK_WORKSPACE_SUFFIX = '_running'


def is_finished_task_workspace_name(basename):
    """Judge whether the directory name is the finished task directory.
    """
    return (
        basename.startswith(TaskType.train.name)
        or basename.startswith(TaskType.evaluate.name)) \
        and not basename.endswith(_RUNNING_TASK_WORKSPACE_SUFFIX)


class TaskManager:
    """Task manager, a resident process to manager task in client.

    Args:
        client_config: config from client started.
    """
    def __init__(self, client_config):
        self.__client_id = client_config["client_id"]
        self.__client_config = client_config

        # Record the running tasks, index by (job_name, round, type)
        self.__tasks = {}

        self.__lmdb = LMDBUtil(client_config['lmdb_path'])

        self.__resource_manager = ResourceManager()
        self.__resource_manager.start()

    def create(self, task_type, task_info, files, grpc_metadata):
        """Create training or evaluation task and execute them.

        Args:
            task_type: training or evaluation task.
            task_info: The task information from server.
            files: Files sent from server.
            grpc_metadata: The metadata in the grpc header, sent from the
                coordinator, contains model-id, client_id.
        """
        self.__assert_task_not_exist(task_type, task_info)
        self.__merge_resource_setting(task_info.spec.resource)

        self.__create(task_type, task_info, files, grpc_metadata)

    def stop(self, task_type, task_metadata):
        """Stop task.

        Args:
            task_type: training or evaluation task.
            task_metadata: The task metadata.
        """
        index_key = (task_metadata.job_name, task_metadata.round,
                     task_type)
        if index_key in self.__tasks:
            task = self.__tasks[index_key]
            task.cancel()
        else:
            logging.warning("The job of name: %s, round: %s, "
                            "type %s not exist, no need to stop."
                            % index_key)

    def __assert_task_not_exist(self, task_type, task_info):
        name = task_info.metadata.job_name
        round_id = task_info.metadata.round
        if (name, round_id, task_type) in self.__tasks:
            raise ParameterError('The job of name: %s, round: %s, '
                                 'type %s already exist.'
                                 % (name, round_id, task_type))

    def __merge_resource_setting(self, remote):
        """Merge the local and remote resource setting for task.
        If the local resource setting is set, use the local one first.
        """
        local = self.__client_config.get('resource', None)
        if not local:
            return

        def get_valid_value(local_value, remote_value):
            if local_value > 0 and (local_value < remote_value
                                    or remote_value == 0):
                return local_value
            return remote_value

        remote.cpu = get_valid_value(local.get('cpu', 0), remote.cpu, )
        remote.memory = get_valid_value(local.get('memory', 0), remote.memory)
        remote.gpu = get_valid_value(local.get('gpu', 0), remote.gpu)

    def __gen_resource_request(self, resource):
        return {"worker_num": resource.worker_num,
                "worker_resource": {"cpu": resource.cpu,
                                    "gpu": resource.gpu,
                                    "memory": resource.memory}}

    def __create(self, task_type, task_info, files, grpc_metadata):
        task_id = self.__gen_task_id(task_type, task_info)
        workspace = self.__create_task_workspace(task_id)
        logging.info('create task:%s, task path:%s', task_id, workspace)

        resource_spec = self.__resource_manager.request(
            task_id, self.__gen_resource_request(task_info.spec.resource))

        task = create_task(
            task_id=task_id,
            task_type=task_type,
            client_config=self.__client_config,
            task_info=task_info,
            files_from_server=files,
            resource=resource_spec,
            workspace=workspace,
            lmdb=self.__lmdb,
            handle_finish=self.__do_finish,
            grpc_metadata=grpc_metadata)

        task.persist()
        self.__add_task(task)

        # Run task in coroutine.
        asyncio.create_task(task.execute())

    def __create_task_workspace(self, task_id):
        task_workspace = os.path.join(
            self.__client_config['workspace'],
            task_id + _RUNNING_TASK_WORKSPACE_SUFFIX)

        os.mkdir(task_workspace)
        return task_workspace

    def __add_task(self, task):
        index_key = (task.job_name, task.round_num, task.task_type)
        self.__tasks[index_key] = task

    def __do_finish(self, task):
        """When task finished, remove it from running tasks.
        """
        self.__resource_manager.release(task.task_id)
        _modify_task_workspace_to_finished(task)

        index_key = (task.job_name, task.round_num, task.task_type)
        del self.__tasks[index_key]

    def __gen_task_id(self, task_type, task_info):
        """Generate task id
        """
        time_str = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
        # k8s pod name's max length is 63. the origin client id's length is 38.
        # this is too long, so truncate the last 8 digits.
        return '%s-%s-%s-%s-%s-%s' % (task_type,
                                      task_info.metadata.job_name,
                                      self.__client_id[-8:],
                                      self.__client_config["port"],
                                      task_info.metadata.round, time_str)

    def get_tasks(self):
        """Get the current tasks.
        """
        return self.__tasks

    def get_resources(self):
        """Get the resource of client.

        TODO: call resource manager to acquire resource state.
        Returns:
            {} means the resources state is private.
        """
        return {}


def _modify_task_workspace_to_finished(task):
    try:
        new_task_workspace = task.workspace.replace(
            _RUNNING_TASK_WORKSPACE_SUFFIX, '')
        os.rename(task.workspace, new_task_workspace)
        logging.info('Modify task path: %s to %s',
                     task.workspace, new_task_workspace)
        task.workspace = new_task_workspace
    except Exception as err:
        logging.warning(str(err))
