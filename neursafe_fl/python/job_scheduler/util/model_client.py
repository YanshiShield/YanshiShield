#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Model store client.
"""

from absl import logging
from neursafe_fl.python.job_scheduler.util.const import MODEL_MANAGER_ADDRESS
from neursafe_fl.python.utils.http_client import HttpClient, HTTPError


class ModelClient:
    """Client to access the model store.

    The operation on model, check model information.
    """

    def __init__(self):
        self.__model_server = MODEL_MANAGER_ADDRESS
        self.__http_client = HttpClient()

    def get_model(self, model_id):
        """Get the specified model version with its id.
        """
        url = "http://%s/api/v1/models?model_id=%s" % (
            self.__model_server, model_id)
        try:
            return self.__http_client.get(url)
        except HTTPError as err:
            logging.error(str(err))
            return None

    def exist(self, model_id):
        """Judge if the model id exist.
        """
        model_info = self.get_model(model_id)
        if model_info:
            return True
        return False
