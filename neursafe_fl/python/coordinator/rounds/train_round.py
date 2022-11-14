#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-many-arguments, no-member
"""Train Round Module."""
from os.path import basename
import pickle

from absl import logging
from neursafe_fl.python.utils.file_io import unzip, zip_files

from neursafe_fl.proto.message_pb2 import Task, TaskSpec, Metadata, File, \
    Scripts, Optimizer
from neursafe_fl.python.coordinator.common.utils import join
from neursafe_fl.python.coordinator.aggregator.weight_aggregator import \
    WeightAggregator
from neursafe_fl.python.coordinator.client_stub import train, stop
from neursafe_fl.python.coordinator.extenders import (broadcast_extender,
                                                      aggregate_extender,
                                                      finish_extender)
from neursafe_fl.python.coordinator.rounds.base_round import BaseRound, \
    PACKAGE_IO_NAME
from neursafe_fl.python.runtime.runtime_factory import RuntimeFactory


class TrainRound(BaseRound):
    """Federate learning train round.

    TrainRound used for training machine learning or deep learning model.

    Start the round and process the data during the execution of round. The
    workflow is controlled by RoundController.
    It has the default process, and also support extender(custom) process.
    Typically, it only process the broadcast data, client's upload data.

    Attributes:
        __extender_process: flag for whether to execute the extender process
    """

    def __init__(self, config, round_id, workspace, model, ssa_server=None):
        super().__init__(config, round_id, workspace, model)
        self.__extenders = config.get("extenders")
        self.__extender_process = bool(self.__extenders)

        # aggregator default use the libs' weight_aggregator
        # TODO later aggregator will be created by configuration
        #  also support the user's custom aggregator.
        self.__aggregator = WeightAggregator(ssa_server)

        self.__broadcast_task = None  # params broadcast to client
        self.__broadcast_file = None  # file broadcast to client
        self.__extend_params = None  # user custom params for extender func

    def on_prepare(self):
        self.create_compression_if_needed()

        if not self.__broadcast_task:
            self.__broadcast_task = self.__construct_broadcast_task()

        custom = {}
        if self.__extender_process:
            custom = self.__construct_custom_config()
            self.__broadcast_task.spec.custom_params.update(custom["params"])

        files = self._extract_file(custom)
        logging.info(files)
        file_io = zip_files(files)
        file_info = File(name=PACKAGE_IO_NAME, compress=True)
        self.__broadcast_file = (file_info, file_io)

    async def on_broadcast(self, client):
        """Broadcast callback."""
        await train(client, self._config.get("job-id"),
                    self.__broadcast_task, self.__broadcast_file,
                    self._config.get("ssl"))
        logging.info("Broadcast to client %s success.", client)

    def __construct_broadcast_task(self):
        metadata = Metadata(
            job_name=self._config["job_name"],
            round=self._round_id)

        optimizer = Optimizer()
        if self._config.get("optimizer"):
            optimizer_config = self._config["optimizer"]
            optimizer = Optimizer(name=optimizer_config.get("name"))
            if optimizer_config.get("params"):
                optimizer.params.update(optimizer_config["params"])

        resource = self._config.get("resource", {})
        resource = {"cpu": resource.get("cpu", 1.0),
                    "memory": resource.get("memory", 1000),
                    "gpu": resource.get("gpu", 0),
                    "worker_num": resource.get("worker_num", 1)}

        if self._config.get("task_entry"):
            task_spec = TaskSpec(entry_name=self._config["task_entry"],
                                 runtime=self._config["runtime"],
                                 resource=resource, optimizer=optimizer,
                                 datasets=self._config.get("datasets",
                                                           None))
        if self._config.get("scripts"):
            scripts = Scripts(
                path="scripts/%s" % basename(self._config["scripts"]["path"]),
                config_file=self._config["scripts"]["config_file"])
            task_spec = TaskSpec(scripts=scripts,
                                 runtime=self._config["runtime"],
                                 resource=resource, optimizer=optimizer,
                                 datasets=self._config.get("datasets",
                                                           None))

        if self._config.get("parameters"):
            task_spec.params.update(self._config["parameters"])

        if self._config.get("secure_algorithm"):
            if self._config["secure_algorithm"]["type"].lower() == 'ssa':
                self._config["secure_algorithm"]["clients_num"] = \
                    self._config["hyper_parameters"]["client_num"]
                self._config["secure_algorithm"]["aggregate_timeout"] = \
                    self._config["hyper_parameters"]["round_timeout"]
            task_spec.secure_algorithm.update(self._config["secure_algorithm"])

        if self._config.get("compression"):
            task_spec.compression.update(self._config["compression"])

        task = Task(metadata=metadata, spec=task_spec)
        return task

    def __construct_custom_config(self):
        result = {}
        for extender in self.__extenders:
            func = extender.get("broadcast")
            tmp = broadcast_extender(func, self._config.get("parameters"))
            if not result:
                result = tmp
            else:
                result["files"].update(tmp.get("files", {}))
                result["params"].update(tmp.get("params", {}))
        return result

    async def on_aggregate(self, msg, number):
        """Aggregate callback."""
        data = self.__extract_training_result(msg, number)

        self.__aggregator.accumulate(data)

        # extender process: user's extend functions
        if self.__extender_process:
            result = {}
            for extender in self.__extenders:
                func = extender.get("aggregate")
                tmp = aggregate_extender(func, data, self.__extend_params)
                result.update(tmp)
            self.__extend_params = result

    def __extract_training_result(self, msg, number):
        params, files = msg[0], msg[1]
        unzip_path = self._workspace.get_client_upload_dir(self._round_id,
                                                           number)

        def parse_weights(weights_io):
            weights_io.seek(0)
            return pickle.loads(files[0][1].read())

        def parse_custom_configuration():
            if len(files) > 1:
                files_io = files[1][1]
                unzip(files_io, unzip_path)

        def decode_weights_if_needed():
            if self._compression:
                weights_converter = RuntimeFactory.create_weights_converter(
                    self._config["runtime"])

                return weights_converter.decode(weights, self._compression)

            return weights

        parse_custom_configuration()
        weights = parse_weights(files[0][1])
        raw_weights = decode_weights_if_needed()

        return {"weights": raw_weights,
                "custom_files": join(unzip_path, "custom/"),
                "custom_params": params.spec.custom_params,
                "metrics": params.spec.metrics,
                "client_id": params.client_id}

    async def on_finish(self):
        """Finish callback."""
        result = await self.__aggregator.aggregate()

        if self.__extender_process:
            for extender in self.__extenders:
                func = extender.get("finish")
                finish_extender(func, self.__extend_params)

        return result

    async def on_stop(self, client):
        """Stop callback."""
        metadata = Metadata(job_name=self._config["job_name"],
                            round=self._round_id)
        await stop(client, metadata, "train", self._config.get("ssl"))
        logging.info("Train round process is stopped.")
