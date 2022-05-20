#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Cloud Task."""

from os.path import join, dirname, abspath
from tornado import gen
from absl import logging

from neursafe_fl.python.libs.cloud.const import K8S_ADDR, CLOUD_OS, GPU_RS_KEY
from neursafe_fl.python.libs.cloud.k8s_resource_object import K8sPod, \
    K8sService, ServiceCreateFailed, PodExisted, \
    PodCreateFailed, ServiceDeleteFailed, PodDeleteFailed, \
    PodNotExist, ServiceNotExist, ServiceGetFailed, PodGetFailed, ServiceExisted
from neursafe_fl.python.utils.collection_builder import CollectionBuilder
from neursafe_fl.python.utils.file_io import read_json_file


class TaskCreateFailed(Exception):
    """Failed to create TASK."""


class TaskExisted(TaskCreateFailed):
    """Task already exists."""


class TaskDeleteFailed(Exception):
    """Failed to delete TASK."""


class TaskGetFailed(Exception):
    """Failed to get TASK."""


class TaskNotExist(Exception):
    """The TASK does not exist."""


class BaseTask:
    """"""

    @gen.coroutine
    def create(self, **task):
        """

        Returns:
            TASK: Ignore.

        Raises:
            TaskExisted: Ignore.
            TaskCreateFailed: Ignore.
        """

    @gen.coroutine
    def delete(self, name, namespace):
        """

        Returns:
            TASK: Ignore.

        Raises:
            TaskNotExist: Ignore.
            TaskDeleteFailed: Ignore.
        """

    @gen.coroutine
    def get(self, name, namespace):
        """

        Returns:
            TASK: Ignore.

        Raises:
            TaskNotExist: Ignore.
            TaskGetFailed: Ignore.
        """


class K8sTask(BaseTask):
    """Task in Kubernetes.

    Attentions:
        1. Only supports a single container.
        2. All task pods run under the default namespace of k8s.
            TODO: namespace create, delete.
    """

    POD_YAML_TEMPLATE_PATH = join(
        dirname(abspath(__file__)), 'pod_template.json')
    SERVICE_YAML_TEMPLATE_PATH = join(
        dirname(abspath(__file__)), 'service_template.json')

    def __init__(self, service_creating=True):
        super().__init__()
        self.__pod = K8sPod(K8S_ADDR)
        self.__service = K8sService(K8S_ADDR) if service_creating else None

        self.__pod_yaml_template = read_json_file(
            self.POD_YAML_TEMPLATE_PATH)
        self.__service_yaml_template = read_json_file(
            self.SERVICE_YAML_TEMPLATE_PATH)

    @gen.coroutine
    def create(self, **task):
        """Create task in kubernetes.

        TODO: A service leak occurs, when task fails.
            (service succeeds, pod failed)

        Args:
            task: {
                'name': 'pytorch-mnist-job',
                'namespace': 'default',
                'cmds': ['python3.7', '-m', 'neursafe_fl.python.coordinator.app'],
                'port': 50051,
                'image': 'fl-coordinator:latest',
                'volumes': [('name', '/path/to/src','/path/to/desc'),],
                'envs': {'env_name': 'env_value'},
                'resources': {'cpu': 1.0, 'memory': 20}
                    # cpu unit: m, mem unit: Mi
                'state': 'Pending|Running|Failed|Succeeded|Unknown',
                "node_id": "10.10.10.10",
                "wording_dir": "/root/fl"
            }

        Returns:
            TASK: Ignore.

        Raises:
            TaskExisted: Ignore.
            TaskCreateFailed: Ignore.
        """
        name = task['name']
        namespace = task.get('namespace', 'default')
        cmds = task.get('cmds', [])
        port = task.get('port', None)
        envs = task.get('envs', {})
        image = task['image']
        volumes = task.get('volumes', [])
        node_id = task.get("node_id")
        resources = task.get("resources", {})
        working_dir = task.get("working_dir")

        try:
            if self.__service:
                yield self.__create_service(name, namespace, port)

            pod = yield self.__create_pod(name, namespace, cmds, envs,
                                          port, image, volumes, node_id,
                                          resources, working_dir)

            task['state'] = pod['status']['phase']
            raise gen.Return(task)
        except (ServiceExisted, PodExisted) as err:
            logging.exception(str(err))
            raise TaskExisted('Task(%s:%s) exists.' % (
                namespace, name)) from err
        except (ServiceCreateFailed, PodCreateFailed) as err:
            logging.exception(str(err))
            raise TaskCreateFailed('Failed to create task(%s:%s).' % (
                namespace, name)) from err

    @gen.coroutine
    def __create_service(self, service_name, namespace, port):
        def construct_service_spec():
            params = {
                'name': service_name,
                'namespace': namespace,
                'port': port,
            }

            service_spec = CollectionBuilder(
                self.__service_yaml_template,
                params,
                keep_original_type_keys=['port', 'targetPort']
            ).format()

            logging.debug(service_spec)
            return service_spec

        service_spec = construct_service_spec()
        yield self.__service.create(service_spec)

    # pylint: disable=too-many-arguments
    @gen.coroutine
    def __create_pod(self, pod_id, namespace, cmds, envs,
                     port, image, volumes, node_id, resources, working_dir):
        pod_spec = self.__construct_pod_spec(
            pod_id, namespace, cmds, envs,
            port, image, volumes, node_id, resources, working_dir)

        pod = yield self.__pod.create(pod_spec)
        raise gen.Return(pod)

    # pylint: disable=too-many-arguments, unused-argument, too-many-locals
    def __construct_pod_spec(self, pod_id, namespace, cmds, envs,
                             port, image, volumes, node_id, resources,
                             working_dir):
        params = {
            'pod_name': pod_id,
            'namespace': namespace,
            'container_name': pod_id,
            'image': image,
            'imagePullPolicy': 'IfNotPresent',
            'port': port,
        }

        pod_spec = CollectionBuilder(
            self.__pod_yaml_template,
            params,
            keep_original_type_keys=['containerPort']
        ).format()

        container_spec = pod_spec['spec']['containers'][0]
        if resources:
            container_spec["resources"]["request"] = {
                "cpu": str(resources.get("cpu", 0)),
                "memory": str(resources.get("memory", 0)),
                GPU_RS_KEY: str(resources.get(GPU_RS_KEY, 0))
            }

        if working_dir:
            container_spec["workingDir"] = working_dir

        if node_id:
            pod_spec["spec"]["nodeSelector"] = {
                "kubernetes.io/hostname": node_id}

        def add_volumes():
            def add_volume(name, src, dest):
                pod_spec['spec']['volumes'].append(
                    {'name': name, 'hostPath': {'path': src}})
                container_spec['volumeMounts'].append(
                    {'name': name, 'mountPath': dest})

            for name, src, dest in volumes:
                add_volume(name, src, dest)

        def add_envs():
            for name, value in envs.items():
                container_spec['env'].append(
                    {'name': name, 'value': value})

        add_volumes()
        add_envs()

        container_spec['command'] = cmds
        logging.debug(pod_spec)

        return pod_spec

    @gen.coroutine
    def delete(self, name, namespace):
        """Delete Task in kubernetes.

        Returns:
            TASK: Ignore.

        Raises:
            TaskNotExist: Ignore.
            TaskDeleteFailed: Ignore.
        """
        try:
            if self.__service:
                yield self.__service.delete(name, namespace)
        except ServiceNotExist as err:
            logging.exception(str(err))
        except ServiceDeleteFailed as err:
            logging.exception(str(err))
            raise TaskDeleteFailed('Failed to delete task(%s:%s).' % (
                namespace, name)) from err

        try:
            pod = yield self.__pod.delete(name, namespace)
            raise gen.Return(self.__convert_pod_to_task(pod))
        # TOOD: Optimize exception logic.
        except PodNotExist as err:
            logging.exception(str(err))
            raise TaskNotExist('Task(%s:%s) unexist.' % (
                namespace, name)) from err
        except PodDeleteFailed as err:
            logging.exception(str(err))
            raise TaskDeleteFailed('Failed to delete task(%s:%s).' % (
                namespace, name)) from err

    @gen.coroutine
    def get(self, name, namespace):
        """

        Returns:
            TASK: Ignore.

        Raises:
            TaskNotExist: Ignore.
            TaskGetFailed: Ignore.
        """
        try:
            if self.__service:
                yield self.__service.get(name, namespace)
        except ServiceNotExist as err:
            logging.error(str(err))
        except ServiceGetFailed as err:
            logging.error(str(err))
            raise TaskGetFailed('Failed to get task(%s:%s).' % (
                namespace, name)) from err

        try:
            pod = yield self.__pod.get(name, namespace)
            raise gen.Return(self.__convert_pod_to_task(pod))
        except PodNotExist as err:
            logging.error(str(err))
            raise TaskNotExist('Task(%s:%s) unexist.' % (
                namespace, name)) from err
        except PodGetFailed as err:
            logging.error(str(err))
            raise TaskGetFailed('Failed to get task(%s:%s).' % (
                namespace, name)) from err

    def __convert_pod_to_task(self, pod):
        # ignore: envs, resources, volumes
        # TODO: 'port': container_spec['ports'][0]['containerPort']
        container_spec = pod['spec']['containers'][0]
        return {
            'name': pod['metadata']['name'],
            'namespace': pod['metadata']['namespace'],
            'cmds': container_spec.get('command', None),
            'image': container_spec['image'],
            'state': pod['status']['phase']
        }


class DockerSwarmTask(BaseTask):
    """"""


TASK = {'k8s': K8sTask(), 'docker_swarm': DockerSwarmTask()}[CLOUD_OS]
