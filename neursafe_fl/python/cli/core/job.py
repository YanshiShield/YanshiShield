#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Federated learning job, used to operate job."""

import json

from absl import logging
import urllib3


class Job:
    """Federated learning job."""
    def __init__(self, api_server):
        self.__api_server = api_server
        self.__http_client = urllib3.PoolManager()

    def create(self, namespace, job_config):
        """Create job."""
        url = "http://%s/api/v1/namespaces/%s/jobs" % (
            self.__api_server, namespace)

        resp = self.__http_client.request(
            "POST", url,
            headers={"Content-type": "application/json"},
            body=json.dumps(job_config))
        if resp.status in (200, 201):
            return
        raise Exception(_get_error_msg(resp))

    def update(self, namespace, job_config):
        """Update job."""
        url = "http://%s/api/v1/namespaces/%s/jobs/%s" % (
            self.__api_server, namespace, job_config["id"])

        resp = self.__http_client.request(
            "PUT", url,
            headers={"Content-type": "application/json"},
            body=json.dumps(job_config))
        if resp.status == 200:
            return
        raise Exception(_get_error_msg(resp))

    def get_jobs(self, namespace):
        """Get jobs."""
        url = "http://%s/api/v1/namespaces/%s/jobs" % (
            self.__api_server, namespace)

        resp = self.__http_client.request("GET", url)
        if resp.status == 200:
            return json.loads(resp.data)
        raise Exception(_get_error_msg(resp))

    def get_job(self, namespace, job_id):
        """Get job."""
        url = "http://%s/api/v1/namespaces/%s/jobs/%s" % (
            self.__api_server, namespace, job_id)

        resp = self.__http_client.request("GET", url)
        if resp.status == 200:
            return json.loads(resp.data)
        raise Exception(_get_error_msg(resp))

    def delete(self, namespace, job_id):
        """Delete job."""
        url = "http://%s/api/v1/namespaces/%s/jobs/%s" % (
            self.__api_server, namespace, job_id)

        resp = self.__http_client.request("DELETE", url)
        if resp.status == 200:
            return
        raise Exception(_get_error_msg(resp))

    def start(self, namespace, job_id):
        """Start job."""
        url = "http://%s/api/v1/namespaces/%s/jobs/%s:start" % (
            self.__api_server, namespace, job_id)

        resp = self.__http_client.request(
            "PUT", url,
            headers={"Content-type": "application/json"},
            body=json.dumps(None))
        if resp.status == 200:
            return
        raise Exception(_get_error_msg(resp))

    def stop(self, namespace, job_id):
        """Stop job."""
        url = "http://%s/api/v1/namespaces/%s/jobs/%s:stop" % (
            self.__api_server, namespace, job_id)

        resp = self.__http_client.request(
            "PUT", url,
            headers={"Content-type": "application/json"},
            body=json.dumps(None))
        if resp.status == 200:
            return
        raise Exception(_get_error_msg(resp))

    def check_health(self):
        """Check health"""
        url = "http://%s/api/v1/health" % (
            self.__api_server)

        resp = self.__http_client.request("GET", url)
        if resp.status == 200:
            return
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
