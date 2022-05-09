#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Resource object on cloud."""

import json
from abc import abstractmethod
from absl import logging
from tornado import httpclient, gen

from neursafe_fl.python.libs.cloud.const import K8S_API_TOKEN, K8S_API_PROTOCOL


class PodCreateFailed(Exception):
    """Failed to create pod."""


class PodExisted(PodCreateFailed):
    """Pod already exists."""


class PodDeleteFailed(Exception):
    """Failed to delete pod."""


class PodGetFailed(Exception):
    """Failed to get pod."""


class PodNotExist(Exception):
    """The pod does not exist."""


class ServiceCreateFailed(Exception):
    """Failed to create service."""


class ServiceExisted(ServiceCreateFailed):
    """Service already exists."""


class ServiceDeleteFailed(Exception):
    """Failed to delete service."""


class ServiceGetFailed(Exception):
    """Failed to get service."""


class ServiceNotExist(Exception):
    """The service does not exist."""


class ResourceObject:
    """Cloud object."""

    def __init__(self, cloud_addr):
        self._transfer = _Transfer(cloud_addr)

    @abstractmethod
    def create(self, cfg):
        """Create resource object.
        """

    @abstractmethod
    def get(self, name, namespace):
        """Get resource object.
        """

    @abstractmethod
    def delete(self, name, namespace):
        """Delete resource object.
        """


class K8sService(ResourceObject):
    """k8s service."""

    @gen.coroutine
    def create(self, cfg):
        """Create service.

        Returns:
            SERVICE object.

        Raises:
            ServiceExisted: Service already exists.
            ServiceCreateFailed: Failed to create service.
        """
        namespace = cfg['metadata'].get('namespace', 'default')
        url = '/api/v1/namespaces/%s/services' % namespace

        body = json.dumps(cfg)
        http_code, body = yield self._transfer.trans_msg(url, 'POST', body)
        logging.debug('%d, %s', http_code, body)

        if http_code == 201:
            raise gen.Return(body)

        if http_code == 409:
            raise ServiceExisted(body)

        raise ServiceCreateFailed(body)

    @gen.coroutine
    def get(self, name, namespace='default'):
        """Get SERVICE.

        Returns:
            SERVICE object.

        Raises:
            ServiceNotExist: SERVICE not exist.
            ServiceGetFailed: Failed to get SERVICE.
        """
        url = '/api/v1/namespaces/%s/services/%s' % (namespace, name)
        http_code, body = yield self._transfer.trans_msg(url, 'GET')
        logging.debug('%d, %s', http_code, body)

        if http_code == 200:
            raise gen.Return(body)

        if http_code == 404:
            raise ServiceNotExist(body)

        raise ServiceGetFailed(body)

    @gen.coroutine
    def delete(self, name, namespace='default'):
        """Delete SERVICE.

        Returns:
            SERVICE STATUS object. {'kind': 'Status', 'apiVersion': 'v1',
                'metadata': {}, 'status': 'Success'}

        Raises:
            ServiceNotExist: SERVICE not exist.
            ServiceDeleteFailed: Failed to create SERVICE.
        """
        url = '/api/v1/namespaces/%s/services/%s' % (namespace, name)
        http_code, body = yield self._transfer.trans_msg(url, 'DELETE')
        logging.debug('%d, %s', http_code, body)

        if http_code == 200:
            raise gen.Return(body)

        if http_code == 404:
            raise ServiceNotExist(body)

        raise ServiceDeleteFailed(body)


class K8sPod(ResourceObject):
    """k8s pod."""

    @gen.coroutine
    def create(self, cfg):
        """Create pod.

        Returns:
            POD object.

        Raises:
            PodExisted: Pod already exists.
            PodCreateFailed: Failed to create pod.
        """
        namespace = cfg['metadata'].get('namespace', 'default')
        url = '/api/v1/namespaces/%s/pods' % namespace

        body = json.dumps(cfg)
        http_code, body = yield self._transfer.trans_msg(url, 'POST', body)
        logging.debug('%d, %s', http_code, body)

        if http_code == 201:
            raise gen.Return(body)

        if http_code == 409:
            raise PodExisted(body)

        raise PodCreateFailed(body)

    @gen.coroutine
    def get(self, name, namespace='default'):
        """Get pod.

        Returns:
            POD object.

        Raises:
            PodNotExist: Pod not exist.
            PodGetFailed: Failed to get pod.
        """
        url = '/api/v1/namespaces/%s/pods/%s' % (namespace, name)
        http_code, body = yield self._transfer.trans_msg(url, 'GET')
        logging.debug('%d, %s', http_code, body)

        if http_code == 200:
            raise gen.Return(body)

        if http_code == 404:
            raise PodNotExist(body)

        raise PodGetFailed(body)

    @gen.coroutine
    def delete(self, name, namespace='default'):
        """Delete pod.

        Returns:
            POD object.

        Raises:
            PodNotExist: Pod not exist.
            PodDeleteFailed: Failed to create pod.
        """
        url = '/api/v1/namespaces/%s/pods/%s' % (namespace, name)
        http_code, body = yield self._transfer.trans_msg(url, 'DELETE')
        logging.debug('%d, %s', http_code, body)

        if http_code == 200:
            raise gen.Return(body)

        if http_code == 404:
            raise PodNotExist('Pod not exist, pod id: %s' % name)

        raise PodDeleteFailed(
            'Delete pod failed, http code: %s, err info: %s' % (
                http_code, body))


class _Transfer:  # pylint: disable=too-few-public-methods
    """Message transfer.
    """

    def __init__(self, cloud_addr, protocol=K8S_API_PROTOCOL):
        self.__http_client = httpclient.AsyncHTTPClient(
            None, defaults=dict(request_timeout=10))
        self.__prefix_url = protocol + '://' + cloud_addr

        self.__headers = {'Content-Type': 'application/json'}
        if protocol == 'https':
            token = K8S_API_TOKEN
            self.__headers['Authorization'] = 'Bearer ' + token

    @gen.coroutine
    def trans_msg(self, suffix_url, method, body=None, validate_cert=False):
        """Transfer POST/PUT/DELETE/GET message.

        Returns:
            (response_code, string/dict))

        Raises:
            Don't throw exception.
        """
        try:
            url = self.__prefix_url + suffix_url

            resp = yield self.__http_client.fetch(
                url, method=method, headers=self.__headers, body=body,
                validate_cert=validate_cert)

            raise gen.Return((resp.code, json.loads(resp.body)))

        except httpclient.HTTPError as http_error:
            if http_error.response:
                err_msg = json.loads(http_error.response.body)
            else:
                err_msg = str(http_error)

            raise gen.Return((http_error.code, err_msg))
        # TODO: Handle other exception.
