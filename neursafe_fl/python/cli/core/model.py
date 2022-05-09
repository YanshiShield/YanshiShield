#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Model module to access the model manager.
"""

import json

from absl import logging
import urllib3


class Model:
    """Agent to access the model manager

    The operation on model, create, get and delete model.
    """

    def __init__(self, api_server):
        self.__api_server = api_server
        self.__http_client = urllib3.PoolManager()

    def get_models(self, namespace):
        """Get all the models in namespace.
        """
        url = "http://%s/api/v1/namespaces/%s/models" % (
            self.__api_server, namespace)

        resp = self.__http_client.request("GET", url)
        if resp.status == 200:
            return json.loads(resp.data).get("models")
        if resp.status == 404:
            return []
        raise Exception(_get_error_msg(resp))

    def get_model(self, namespace, name, version=None):
        """Get one model all the versions or specified version with a list.
        """
        if version:
            url = "http://%s/api/v1/namespaces/%s/models/%s?version=%s" % (
                self.__api_server, namespace, name, version)
        else:
            url = "http://%s/api/v1/namespaces/%s/models/%s" % (
                self.__api_server, namespace, name)
        resp = self.__http_client.request("GET", url)
        if resp.status == 200:
            return json.loads(resp.data).get("models")
        raise Exception(_get_error_msg(resp))

    def delete(self, namespace, name, version=None):
        """Delete model in the namespace.
        """
        if version:
            url = "http://%s/api/v1/namespaces/%s/models/%s?version=%s" % (
                self.__api_server, namespace, name, version)
        else:
            url = "http://%s/api/v1/namespaces/%s/models/%s" % (
                self.__api_server, namespace, name)

        resp = self.__http_client.request("DELETE", url)
        if resp.status == 200:
            return
        raise Exception(_get_error_msg(resp))

    def create(self, namespace, config):
        """Create model in namespace.
        """
        url = "http://%s/api/v1/namespaces/%s/models" % (
            self.__api_server, namespace)

        resp = self.__http_client.request(
            "POST", url,
            headers={"Content-type": "application/json"},
            body=json.dumps(config))
        if resp.status in (200, 201):
            return json.loads(resp.data)
        raise Exception(_get_error_msg(resp))

    def upload_progress(self, model_id, progress_info):
        """Update the progress of uploading model.
        """
        url = "http://%s/api/v1/models?model_id=%s" % (
            self.__api_server, model_id)

        resp = self.__http_client.request(
            "PUT", url,
            headers={"Content-type": "application/json"},
            body=json.dumps(progress_info))
        if resp.status in (200, 201):
            return json.loads(resp.data)
        raise Exception(_get_error_msg(resp))

    def get_model_by_id(self, model_id):
        """Get the specified model version with its id.
        """
        url = "http://%s/api/v1/models?model_id=%s" % (
            self.__api_server, model_id)
        resp = self.__http_client.request("GET", url)
        if resp.status == 200:
            return json.loads(resp.data)
        raise Exception(_get_error_msg(resp))

    def delete_model_by_id(self, model_id):
        """Delete the specified model version with its id.
        """
        url = "http://%s/api/v1/models?model_id=%s" % (
            self.__api_server, model_id)
        resp = self.__http_client.request("DELETE", url)
        if resp.status == 200:
            return json.loads(resp.data)
        raise Exception(_get_error_msg(resp))


def _get_error_msg(resp):
    if resp.data:
        logging.info(resp.data)
        if __check_json_format(resp.data):
            data = json.loads(resp.data)
            if "reason" in data:
                error_msg = str(data["reason"])
            else:
                error_msg = data
        elif isinstance(resp.data, (bytes, str)):
            error_msg = resp.data
        else:
            error_msg = str(resp)
    else:
        error_msg = str(resp)
    return error_msg


def __check_json_format(raw_msg):
    """check json format.
    """
    if isinstance(raw_msg, (bytes, str)):
        try:
            json.loads(raw_msg)
            return True
        except ValueError:
            return False
    return False
