#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Base Round Module."""

import abc
from os.path import basename

from absl import logging

from neursafe_fl.python.coordinator.common.utils import join
from neursafe_fl.python.coordinator.common.workspace import Files
from neursafe_fl.python.coordinator.round_controller import RoundController

PACKAGE_IO_NAME = "package.zip"


class BaseRound:
    """Define the interfaces of Round.

    Round's main process will be controlled by RoundController. Round only need
    to implement the abstract interfaces in this class.
    """

    def __init__(self, config, round_id, workspace, model):
        self._config = config
        self._round_id = round_id
        self._workspace = workspace
        self._model = model
        self._round_controller = None

    async def run(self):
        """Start the round execution."""
        hyper_params = self._config["hyper_parameters"]
        self._round_controller = RoundController(hyper_params,
                                                 self._config)
        return await self._round_controller.run(self)

    async def process(self, msg):
        """Process the message uploaded from the clients."""
        await self._round_controller.process_msg(msg)

    async def stop(self):
        """Stop the current round."""
        await self._round_controller.stop()

    @abc.abstractmethod
    def on_prepare(self):
        """Prepare task config to broadcast to client."""

    @abc.abstractmethod
    async def on_broadcast(self, client):
        """Generate the params and broadcast to client.

        Args:
            client: client service address to be called.
        Returns:
            None
        """

    @abc.abstractmethod
    async def on_aggregate(self, msg, number):
        """Aggregate the updates uploaded by client.

        Args:
            msg: client's upload data, including training metrics, weights .etc
            number: the serial number of the uploaded client update.
        Returns:
            None
        """

    @abc.abstractmethod
    async def on_finish(self):
        """Finish the round, usually returns the result of round.

        Returns:
            result of the rounds, such as aggregated weights, metrics .etc
        """

    @abc.abstractmethod
    async def on_stop(self, client):
        """Stop the round, typically stopped by user.

        Returns:
            None
        """

    def _extract_file(self, custom):
        files = []
        weight_file = self._create_weights_file()
        files.append((basename(weight_file), weight_file))

        if custom.get("files"):
            custom_files = custom["files"]
            for filename, path in custom_files.items():
                files.append(("prepared/%s" % filename, path))

        if self._config.get("scripts"):
            script_path = self._config["scripts"]["path"]
            files.append(("scripts/%s" % basename(script_path), script_path))

        return files

    def _create_weights_file(self):
        """Save the server aggregated model's weights to file."""
        filename = self._workspace.get_runtime_file_by(Files.InitWeights,
                                                       self._model.runtime)
        file_path = join(self._workspace.get_round_dir(self._round_id),
                         filename)
        self._model.save_weights(file_path)
        logging.info("Save round init weights to %s", file_path)
        return file_path
