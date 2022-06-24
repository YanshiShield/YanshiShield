#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Proxy module.
"""

import os
import json

from tornado.httpclient import AsyncHTTPClient, HTTPError

PROXY_ADDRESS = os.getenv("PROXY_ADDRESS", "localhost:8080")
TOKEN = os.getenv("TOKEN")


class ProxyError(Exception):
    """Proxy handle route rules request error."""


class Proxy:
    """Proxy class mainly provide interface adaptation of Proxy component.

    It provide the Add, Delete, Modify and Get operations on the route rules of
    internal module. Typically, the route rule is: <module-id, module-service>.
    This class will inject the rules into the proxy configuration.
    And as the reverse proxy, the Proxy component will route the request
    base on the new configuration.
    """

    def __init__(self):
        self.__proxy_client = AsyncHTTPClient()
        self.__token = TOKEN

    async def add(self, namespace, job_id, service):
        """add route rule, if exist, old rule will be replaced."""
        module_id = self.__module_id(namespace, job_id)
        await self.__fetch("POST", module_id, service)

    async def get(self, namespace, job_id):
        """get exist route rule."""
        module_id = self.__module_id(namespace, job_id)
        _, service = await self.__fetch("GET", module_id)
        return service

    async def delete(self, namespace, job_id):
        """delete exist route rule."""
        module_id = self.__module_id(namespace, job_id)
        await self.__fetch("DELETE", module_id)

    async def modify(self, namespace, job_id, service):
        """modify exist route rule to new rule."""
        module_id = self.__module_id(namespace, job_id)
        await self.__fetch("PUT", module_id, service)

    def __module_id(self, namespace, job_id):
        return "%s-%s" % (namespace, job_id)

    async def __fetch(self, method, module_id, service=None):
        url = "http://%s/api/v1/internal/routers" % PROXY_ADDRESS
        body = None
        headers = {"module-id": module_id,
                   "token": self.__token}

        if service:
            headers["module-service"] = service

        if method in ["POST", "PUT"]:
            body = json.dumps({})
        try:
            res = await self.__proxy_client.fetch(url, method=method,
                                                  headers=headers, body=body)
            return res.code, res.body
        except (HTTPError, ConnectionError, OSError) as err:
            raise ProxyError(str(err)) from err
