#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=no-member
"""Evaluate Round Module."""
from os.path import basename

from absl import logging
from neursafe_fl.python.utils.file_io import zip_files

from neursafe_fl.proto.message_pb2 import File, Metadata, TaskSpec, Scripts, \
    Task, Optimizer
from neursafe_fl.python.coordinator.aggregator.weight_aggregator import \
    WeightAggregator
from neursafe_fl.python.coordinator.client_stub import evaluate, stop
from neursafe_fl.python.coordinator.extenders import broadcast_extender
from neursafe_fl.python.coordinator.rounds.base_round import BaseRound, \
    PACKAGE_IO_NAME


class EvaluateRound(BaseRound):
    """Federate learning evaluate round.

    EvaluateRound used for evaluating machine learning or deep learning model.
    Also user can extender the evaluate round.
    """

    def __init__(self, config, round_id, workspace, model):
        super().__init__(config, round_id, workspace, model)
        self.__extenders = config.get("extenders")
        self.__extender_process = bool(self.__extenders)

        # aggregator default use the libs' weight_aggregator
        # TODO later aggregator will be created by configuration
        #  also support the user's custom aggregator.
        self.__aggregator = WeightAggregator()
        self.__broadcast_task = None
        self.__broadcast_file = None

    def on_prepare(self):
        if not self.__broadcast_task:
            self.__broadcast_task = self.__construct_broadcast_task()

        custom = {}
        if self.__extender_process:
            custom = self.__construct_custom_config()
            self.__broadcast_task.spec.custom_params.update(custom["params"])

        files = self._extract_file(custom)
        file_io = zip_files(files)
        file_info = File(name=PACKAGE_IO_NAME, compress=True)
        self.__broadcast_file = (file_info, file_io)

    async def on_broadcast(self, client):
        await evaluate(client, self._config.get("job-id"),
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

        loss = self._gen_loss_config()

        resource = self._config.get("resource", {})
        resource = {"cpu": resource.get("cpu", 1.0),
                    "memory": resource.get("memory", 1000),
                    "gpu": resource.get("gpu", 0),
                    "worker_num": resource.get("worker_num", 1)}

        if self._config.get("task_entry"):
            task_spec = TaskSpec(entry_name=self._config["task_entry"],
                                 runtime=self._config["runtime"],
                                 resource=resource, optimizer=optimizer,
                                 loss=loss,
                                 datasets=self._config.get("datasets",
                                                           None))
        if self._config.get("scripts"):
            scripts = Scripts(
                path="scripts/%s" % basename(self._config["scripts"]["path"]),
                config_file=self._config["scripts"]["config_file"])
            task_spec = TaskSpec(scripts=scripts,
                                 runtime=self._config["runtime"],
                                 resource=resource, optimizer=optimizer,
                                 loss=loss,
                                 datasets=self._config.get("datasets",
                                                           None))

        if self._config.get("parameters"):
            task_spec.params.update(self._config["parameters"])

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
        data = {"metrics": msg[0].spec.metrics}
        self.__aggregator.accumulate(data)

        if self.__extender_process:
            logging.debug("Evaluate aggregate process extend not supported.")

    async def on_finish(self):
        result = await self.__aggregator.aggregate()
        if self.__extender_process:
            logging.debug("Evaluate finish process extend not supported.")

        return result

    async def on_stop(self, client):
        """Stop callback."""
        metadata = Metadata(job_name=self._config["job_name"],
                            round=self._round_id)

        await stop(client, metadata, "evaluate", self._config.get("ssl"))
        logging.info("Evaluate round process is stopped.")
