#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Http client
"""

import json
import urllib3
from urllib3.exceptions import HTTPError


class HttpClient:
    """http client class.
    """

    def __init__(self):
        self.__client = urllib3.PoolManager()
        self.__default_headers = {"Content-type": "application/json"}

    def get(self, url, headers=None):
        """GET method
        """
        if not headers:
            headers = self.__default_headers
        resp = self.__client.request("GET", url, headers=headers)
        if resp.status in (200, 201):
            return json.loads(resp.data)
        raise HTTPError(_get_error_msg(resp))

    def post(self, url, body, headers=None):
        """POST method
        """
        if not headers:
            headers = self.__default_headers
        resp = self.__client.request("POST", url, headers=headers, body=body)
        if resp.status in (200, 201):
            return json.loads(resp.data)
        raise HTTPError(_get_error_msg(resp))

    def delete(self, url, headers=None):
        """DELETE method
        """
        if not headers:
            headers = self.__default_headers
        resp = self.__client.request("DELETE", url, headers=headers)
        if resp.status == 200:
            return
        raise HTTPError(_get_error_msg(resp))

    def put(self, url, body, headers=None):
        """PUT method
        """
        if not headers:
            headers = self.__default_headers
        resp = self.__client.request("PUT", url, headers=headers, body=body)
        if resp.status in (200, 201):
            return json.loads(resp.data)
        raise Exception(_get_error_msg(resp))


def _get_error_msg(resp):
    if resp.data:
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
