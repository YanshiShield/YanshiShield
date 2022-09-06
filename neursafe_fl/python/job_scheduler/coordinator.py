#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Coordinator Create/get/delete."""

from os import mkdir
from os.path import join, exists
from tornado import gen

from absl import logging

from neursafe_fl.python.job_scheduler.util.errors import CoordinatorNotExist, \
    CoordinatorDeleteFailed, CoordinatorExists, \
    CoordinatorGetFailed, CoordinatorCreateFailed
from neursafe_fl.python.libs.cloud.task import TASK, TaskExisted, \
    TaskCreateFailed, TaskNotExist, TaskDeleteFailed, TaskGetFailed
from neursafe_fl.python.libs.cloud.const import K8S_NAMESPACE
from neursafe_fl.python.utils.file_io import write_json_file
import neursafe_fl.python.job_scheduler.util.const as const


class Coordinator:
    """"""

    def __init__(self):
        self.__task = TASK

    @gen.coroutine
    def create(self, job_cfg, workspace, namespace='default'):
        """Create coordinator.

        Returns:
            None

        Raises:
            CoordinatorExists: Ignore.
            CoordinatorCreateFailed: Ignore.
        """
        def prepare_env_cfg():
            if const.STORAGE_TYPE.lower() == "s3":
                return {"REPORT_PERIOD": const.REPORT_PERIOD,
                        "JOB_SCHEDULER_ADDRESS": const.JOB_SCHEDULER_ADDRESS,
                        "SELECTOR_ADDRESS": const.SELECTOR_ADDRESS,
                        "COORDINATOR_WORKSPACE_PATH":
                            const.COORDINATOR_WORKSPACE_PATH,
                        "DEPLOYMENT_WAY": const.DEPLOYMENT_WAY,
                        "STORAGE_TYPE": const.STORAGE_TYPE,
                        "S3_ENDPOINT": const.S3_ENDPOINT,
                        "S3_ACCESS_KEY": const.S3_ACCESS_KEY,
                        "S3_SECRET_KEY": const.S3_SECRET_KEY,
                        "WORKSPACE_BUCKET": const.WORKSPACE_BUCKET}

            return {"REPORT_PERIOD": const.REPORT_PERIOD,
                    "JOB_SCHEDULER_ADDRESS": const.JOB_SCHEDULER_ADDRESS,
                    "SELECTOR_ADDRESS": const.SELECTOR_ADDRESS,
                    "COORDINATOR_WORKSPACE_PATH":
                        const.COORDINATOR_WORKSPACE_PATH,
                    "DEPLOYMENT_WAY": const.DEPLOYMENT_WAY}

        volumes = self.__contruct_volumes(job_cfg, workspace, namespace)
        cmds = ['python3.7', '-m',
                'neursafe_fl.python.coordinator.app', '--config_file',
                job_cfg["config_file"]]
        privileged = const.STORAGE_TYPE.lower() == "s3"

        name = self.__gen_name(namespace, job_cfg['id'])
        try:
            yield self.__task.create(name=name,
                                     namespace=K8S_NAMESPACE,
                                     cmds=cmds,
                                     port=job_cfg.get(
                                         "port", int(const.COORDINATOR_PORT)),
                                     image=const.COORDINATOR_IMAGE,
                                     volumes=volumes,
                                     envs=prepare_env_cfg(),
                                     privileged=privileged)
        except TaskExisted as err:
            logging.exception(str(err))
            raise CoordinatorExists('Coordinator(%s:%s) exists.' % (
                namespace, name)) from err
        except TaskCreateFailed as err:
            logging.exception(str(err))
            raise CoordinatorCreateFailed(
                'Failed to create coordinator(%s:%s).' % (
                    namespace, name)) from err

    def __contruct_volumes(self, job_cfg, workspace, namespace):
        def prepare_startup_cfg_file():
            job_dir = join(workspace, job_cfg["job-id"])
            if not exists(job_dir):
                mkdir(job_dir)

            job_cfg_path = join(job_dir, 'coordinator.json')
            write_json_file(job_cfg_path, job_cfg)

            return join(const.COORDINATOR_WORKSPACE_PATH,
                        const.TEMP_DIR, job_cfg["job-id"], 'coordinator.json')

        if const.STORAGE_TYPE.lower() == "s3":
            volumes = [("devfuse", "/dev/fuse", "/dev/fuse", "host")]
        else:
            volumes = [("workspace", const.WORKSPACE_PVC,
                        const.COORDINATOR_WORKSPACE_PATH, "pvc")]

        if job_cfg.get("model"):
            model_namespace = job_cfg["model"]["model_namespace"]
            model_path = job_cfg["model"]["model_path"]
            job_cfg['model_path'] = join(const.COORDINATOR_WORKSPACE_PATH,
                                         model_namespace,
                                         model_path.lstrip("/"))
        else:
            job_cfg['model_path'] = join(const.COORDINATOR_WORKSPACE_PATH,
                                         namespace,
                                         job_cfg['model_path'].lstrip("/"))

        if "scripts" in job_cfg:
            job_cfg['scripts']['path'] = join(const.COORDINATOR_WORKSPACE_PATH,
                                              namespace,
                                              job_cfg['scripts']['path'])

        if 'ssl' in job_cfg:
            job_cfg["ssl"] = join(const.COORDINATOR_WORKSPACE_PATH,
                                  namespace,
                                  job_cfg["ssl"])

        if ('extender' in job_cfg
                and 'script_path' in job_cfg['extender']):
            job_cfg['extender']['script_path'] = join(
                const.COORDINATOR_WORKSPACE_PATH, namespace,
                job_cfg['extender']['script_path'].lstrip("/"))

        if 'output' in job_cfg:
            job_cfg["output"] = join(
                const.COORDINATOR_WORKSPACE_PATH, namespace,
                job_cfg['output'].lstrip("/"))

        # mount the config file of coordinator, and
        # this config must be placed after other volumes.
        startup_cfg_file_path = prepare_startup_cfg_file()
        job_cfg["config_file"] = startup_cfg_file_path

        return volumes

    @gen.coroutine
    def delete(self, job_id, namespace="default"):
        """Delete coordinator.

        Returns:
            None

        Raises:
            CoordinatorNotExist: Ignore.
            CoordinatorDeleteFailed: Ignore.
        """
        name = self.__gen_name(namespace, job_id)
        try:
            yield self.__task.delete(name=name, namespace=K8S_NAMESPACE)
        except TaskNotExist as err:
            logging.exception(str(err))
            raise CoordinatorNotExist('Coordinator(%s:%s) unexist.' % (
                namespace, name)) from err
        except TaskDeleteFailed as err:
            logging.exception(str(err))
            raise CoordinatorDeleteFailed(
                'Failed to delete coordinator(%s:%s).' % (
                    namespace, name)) from err

    @gen.coroutine
    def status(self, job_id, namespace="default"):
        """Get coordinator status.

        Returns:
            A state dict: For example: {'state': 'RUNNING'}.

        Raises:
            CoordinatorNotExist: Ignore.
            CoordinatorDeleteFailed: Ignore.
        """
        name = self.__gen_name(namespace, job_id)
        try:
            task = yield self.__task.get(name=name, namespace=K8S_NAMESPACE)
            raise gen.Return({'state': task['state'].upper()})
        except TaskNotExist as err:
            logging.error(str(err))
            raise CoordinatorNotExist('Task(%s:%s) unexist.' % (
                namespace, name)) from err
        except TaskGetFailed as err:
            logging.exception(str(err))
            raise CoordinatorGetFailed(
                'Failed to get coordinator(%s:%s).' % (
                    namespace, name)) from err

    def __gen_name(self, namespace, job_name):
        return '%s-%s' % (namespace, job_name)
