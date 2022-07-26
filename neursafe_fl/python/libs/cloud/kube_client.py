#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-few-public-methods
""" kube client, connect to kubernetes
"""

import time
from absl import logging

from kubernetes import watch
import kubernetes.client

from neursafe_fl.python.libs.cloud.const import K8S_ADDR, K8S_API_PROTOCOL, \
    K8S_API_TOKEN
from neursafe_fl.python.libs.cloud.errors import GetNodesError, WatchNodesError


class EventType:
    """Node watch event
    """
    ADD = "ADDED"
    MODIFY = "MODIFIED"
    DELETE = "DELETED"


class KubeClient:
    """kubernetes client
    """

    def __init__(self):
        self.__api_client = self.__init_api_client()
        self.__watch = watch.Watch()

        self.__resource_version = None

    def __init_api_client(self):
        configuration = kubernetes.client.Configuration()
        configuration.host = "%s://%s" % (K8S_API_PROTOCOL, K8S_ADDR)
        configuration.verify_ssl = False
        if K8S_API_PROTOCOL == "https":
            api = kubernetes.client.ApiClient(
                configuration,
                header_name="Authorization",
                header_value="Bearer " + K8S_API_TOKEN)
        else:
            api = kubernetes.client.ApiClient(configuration)
        return kubernetes.client.CoreV1Api(api)

    def get_nodes(self):
        """Return k8s nodes

        Returns:
            nodes: k8s nodes
        """
        try:
            return self.__api_client.list_node().items
        except Exception as error:
            logging.exception(str(error))
            raise GetNodesError("Get k8s nodes exception.") from error

    def watch_nodes(self, callbacks):
        """Watch nodes

        Args:
            callbacks: watch event handle functions.
        """
        try:
            for event in self.__watch.stream(
                    self.__api_client.list_node,
                    resource_version=self.__resource_version):
                event_type = event["type"]
                node_info = event["object"]

                if event_type in [EventType.ADD, EventType.DELETE,
                                  EventType.MODIFY]:
                    callbacks[event_type](node_info)

                self.__update_resource_version(event)
                time.sleep(0)
        except Exception as error:
            logging.exception(str(error))
            raise WatchNodesError("Get k8s nodes exception.") from error

    def __update_resource_version(self, event):
        try:
            self.__resource_version = \
                event["raw_object"]["metadata"]["resourceVersion"]
        except Exception as error:  # pylint:disable=broad-except
            logging.warning("update resource version error, error info: %s",
                            str(error))
