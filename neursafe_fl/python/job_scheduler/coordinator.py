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
        self.__task = TASK  # TODO: 使用单例或者全局变量

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

        name = self.__gen_name(namespace, job_cfg['id'])
        try:
            yield self.__task.create(name=name,
                                     namespace=K8S_NAMESPACE,
                                     cmds=cmds,
                                     port=job_cfg.get(
                                         "port", int(const.COORDINATOR_PORT)),
                                     image=const.COORDINATOR_IMAGE,
                                     volumes=volumes,
                                     envs=prepare_env_cfg())
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
            # Coordinator部分参数只能通过文件进行传递，所以必须将配置写入文件。
            job_dir = join(workspace, job_cfg["job-id"])
            if not exists(job_dir):
                mkdir(job_dir)

            job_cfg_path = join(job_dir, 'coordinator.json')
            write_json_file(job_cfg_path, job_cfg)
            return job_cfg_path

        volumes = []

        def append_volume(name, path):
            if const.DEPLOYMENT_WAY == "cloud":
                path = path.lstrip("/")
                src = join(const.SOURCE_MOUNT_PATH, "%s/%s" % (namespace,
                                                               path))
                dest = join(const.COORDINATOR_WORKSPACE_PATH, path)
            else:
                src, dest = path, path
            volumes.append((name, src, dest))
            return dest

        # change the path to the real path mounted in pod
        if job_cfg.get("model"):  # from model store
            model_namespace = job_cfg["model"]["model_namespace"]
            model_path = job_cfg["model"]["model_path"]
            src = join(const.SOURCE_MOUNT_PATH, "%s/%s" % (
                model_namespace, model_path.lstrip("/")))
            dest = join(const.COORDINATOR_WORKSPACE_PATH,
                        model_path.lstrip("/"))
            volumes.append(("model-path", src, dest))
        else:  # from user namespace
            dest = append_volume('model-path', job_cfg['model_path'])
        job_cfg['model_path'] = dest

        if 'scripts' in job_cfg:
            dest = append_volume('scripts', job_cfg['scripts']['path'])
            job_cfg['scripts']['path'] = dest

        if 'ssl' in job_cfg:
            dest = append_volume('ssl', job_cfg['ssl'])
            job_cfg['ssl'] = dest

        if ('extender' in job_cfg
                and 'script_path' in job_cfg['extender']):
            dest = append_volume('extender-script',
                                 job_cfg['extender']['script_path'])
            job_cfg['extender']['script_path'] = dest

        if 'output' in job_cfg:
            dest = append_volume("output", job_cfg["output"])
            job_cfg["output"] = dest

        # mount the config file of coordinator, and
        # this config must be placed after other volumes.
        startup_cfg_file_path = prepare_startup_cfg_file()
        job_cfg["config_file"] = startup_cfg_file_path
        if const.DEPLOYMENT_WAY == "cloud":
            config_file = "%s/coordinator.json" % job_cfg["job-id"]
            host_dir = join(const.SOURCE_MOUNT_PATH, const.TEMP_DIR)
            host_path = join(host_dir, config_file)
            volumes.append(('entrypoint', host_path, startup_cfg_file_path))

        logging.debug(volumes)
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
