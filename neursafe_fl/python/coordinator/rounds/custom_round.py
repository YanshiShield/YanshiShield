#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Custom Round Module."""
import requests
from absl import logging

from neursafe_fl.python.coordinator.rounds.base_round import BaseRound


class CustomRound(BaseRound):
    """Custom Round Class.

    The CustomRound only process the user's custom(extender) functions.
    User has to define the broadcast extender and aggregate extender, there is
    no default process on the data.
    Typically, user can use this to implement some custom computations.
    """

    def __init__(self, config, round_id, workspace):
        config["hyper_parameters"]["threshold_client_num"] = 0  # no need wait
        config["need_wait"] = False
        super().__init__(config, round_id, workspace, None)

        self.__model = config["model_file"]
        self.__model_metrics = config["metrics"]
        self._deploy_address = config.get("deploy_address")

    def on_prepare(self):
        """prepare the model weights and params to send
        """
        if not self._deploy_address:
            logging.warning("No deploy server address config, will not deploy.")
            return

        logging.info("deploy to %s is ready.", self._deploy_address)

    async def on_broadcast(self, client):
        """Send model and metrics to the deploy client.
        """
        del client  # no need the selected client.
        if not self._deploy_address:
            logging.warning("No deploy server address config, will not deploy.")
            return

        # send the model and params to the deploy server
        result = await self.deploy()
        if result:
            logging.info("Deploy to client %s success.", self._deploy_address)
        else:
            logging.warning("Deploy to client %s failed.", self._deploy_address)

    async def on_aggregate(self, msg, number):
        """Do nothing, there is nothing to aggregate
        """
        logging.warning("This shouldn't be called, deploy need no aggregate")

    async def on_finish(self):
        """Do nothing
        """
        logging.info("Deploy new model to edge finished.")
        return {}

    async def on_stop(self, client):
        """Stop the inference pod, or do nothing.
        """

    async def deploy(self):
        """Deploy the model to node(client).
        """
        url = "http://%s/api/v1/deploy" % self._deploy_address

        metrics = self.__model_metrics
        metrics["round"] = self._round_id
        metrics["runtime"] = "torch"
        files = {'file': open(self.__model, 'rb')}

        res = requests.post(url, data=metrics, files=files)
        if res.status_code == 200:
            return True
        return False
