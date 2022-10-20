#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-many-instance-attributes, too-few-public-methods
"""Trainer Module."""
import json
import asyncio
from absl import logging

from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPError

from neursafe_fl.python.coordinator.grpc_services import Message
from neursafe_fl.python.coordinator.rounds.train_round import TrainRound
from neursafe_fl.python.coordinator.rounds.evaluate_round import EvaluateRound
from neursafe_fl.python.coordinator.rounds.custom_round import CustomRound
from neursafe_fl.python.coordinator.common.workspace import Workspace, Files
from neursafe_fl.python.coordinator.common.utils import join, delete, \
    load_module
from neursafe_fl.python.coordinator.common.types import Statistics, ErrorCode
from neursafe_fl.python.coordinator.fl_model import FlModel
import neursafe_fl.python.coordinator.common.const as const
from neursafe_fl.python.libs.secure.secure_aggregate.ssa import \
    create_ssa_server
from neursafe_fl.python.libs.optimizer import optimizer_config
from neursafe_fl.python.libs.loss import loss_config
from neursafe_fl.python.coordinator.extenders import support_extenders


class State:
    """Define state"""

    STARTING = "STARTING"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    FAILED = "FAILED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"


class _Timer:
    def __init__(self, timeout, callback):
        self.__timeout = timeout
        self.__callback = callback
        self.__task = None

    def start(self):
        """start period timer"""
        self.__task = asyncio.create_task(self.__do_callback())

    async def __do_callback(self):
        await self.__callback()
        await asyncio.sleep(self.__timeout)
        self.__task = asyncio.create_task(self.__do_callback())

    def cancel(self):
        """
        cancel timer
        """
        if self.__task:
            self.__task.cancel()


class Trainer:
    """Trainer control process for federate training job.

    Trainer control the job execution flow, start each round. update the server
    model, and also collect statistics for visualization.

    Notice: trainer do not handle the round_internal error, only control the
            job level workflow.
    """

    def __init__(self, config):
        self.__config = config
        self.__runtime = config["runtime"]
        self.__job_name = config["job_name"]
        self.__hyper_params = config["hyper_parameters"]
        self.__max_rounds = self.__hyper_params["max_round_num"]
        self.__evaluate_interval = self.__hyper_params["evaluate_interval"]
        self.__save_interval = self.__hyper_params["save_interval"]

        self.__round = None
        self.__round_id = 0
        self.__stats = Statistics()

        self.__fl_board = None  # record statistics for visualization
        self.__metrics = []
        self.__checkpoints = {}
        self.__next_ckpt_id = 0

        self.__fl_model = FlModel(config["model_path"], config["runtime"])
        self.__workspace = Workspace(config["output"], config["job_name"])

        self.__http_client = AsyncHTTPClient()
        self.__report_timer = _Timer(const.REPORT_PERIOD,
                                     self.__do_report_progress)

        self.__state = State.STARTING
        self.__force_stop = False

    async def start(self):
        """Start the main process of job."""
        # TODO: client selector get enough resource
        await self.__report_progress_periodically()
        self.__restore_checkpoints()

        self.__fl_model.load()  # load init model
        self.__load_extenders()
        self.__load_optimizer()
        self.__load_loss()

        self.__state = State.RUNNING
        for round_id in range(1, self.__max_rounds + 1):
            if self.__is_training_stop():
                self.stop()
                break

            await self.__run_one_round(round_id)

        logging.info("Federate job finished, statistics:\n%s", self.__stats)
        self.__state = State.STOPPED if self.__force_stop else State.FINISHED
        if self.__stats.success == 0:
            self.__state = State.FAILED
        await self.__stop_report_progress()
        self.finish()

    def __restore_checkpoints(self):
        self.__checkpoints, max_ckpt_id = self.__workspace.get_checkpoints()
        self.__next_ckpt_id = max_ckpt_id + 1

    def stop(self):
        """Stop the main process of job."""
        self.__save_ckpts()

    async def __report_progress_periodically(self):
        if const.JOB_SCHEDULER_ADDRESS:
            self.__report_timer.start()

    async def __do_report_progress(self):
        try:
            url = r"http://%s/api/v1/heartbeat" % const.JOB_SCHEDULER_ADDRESS
            body = {"id": self.__config["job_name"],
                    "namespace": self.__config.get("namespace"),
                    "state": self.__state,
                    "progress": int(self.__stats.progress),
                    "checkpoints": self.__checkpoints}

            req = HTTPRequest(
                url=url,
                method='PUT',
                headers={"Content-type": "application/json"},
                body=json.dumps(body))

            await self.__http_client.fetch(req)
            logging.info('Report progress successfully.')
        except (HTTPError, ConnectionError)as error:
            logging.exception(str(error))

    async def __stop_report_progress(self):
        # before coordinator exit, report last time.
        self.__report_timer.cancel()
        if const.JOB_SCHEDULER_ADDRESS:
            await self.__do_report_progress()

    def __load_extenders(self):
        """Load extender module functions from config file.

        Extenders used to implement user's custom compute or broadcast, there
        include three insertion point:
          broadcast: use for user to add custom files or data to broadcast to
                     clients.
          aggregate: use for user to do custom computation from clients updates.
          finish: use for user to process aggregated result.

        There is no requirement for implementation of extenders, you can
        implement any of them, or none.
        """
        extender_config = self.__config.get("extender")
        self.__config["extenders"] = []

        if extender_config:
            extender = self.__load(extender_config)
            if extender:
                self.__config["extenders"].append(extender)
        else:
            logging.info("No config extenders.")

    def __load(self, extender_config):
        extender = {}
        script_path = extender_config.get("script_path")
        entry = extender_config.get("entry")
        for func in support_extenders:
            extender[func] = load_module(join(script_path, entry),
                                         extender_config.get(func))
        return extender

    def __load_optimizer(self):
        """Load custom extended optimizer.

        The optimizer should be implemented through the extension mechanism.
        Default we implement scaffold as example.

        Then config in file with:
            "optimizer": {
                "name": "scaffold",
                "params": {}
            }
        """
        if self.__config.get("optimizer"):
            optimizer_name = self.__config["optimizer"].get("name")
            optimizer_name = "%s_%s" % (self.__runtime, optimizer_name)
            if optimizer_name in optimizer_config:
                optimizer = self.__load(optimizer_config[optimizer_name])
                if optimizer:
                    self.__config["extenders"].append(optimizer)
                    logging.info("Load optimizer %s success.", optimizer_name)
            else:
                logging.warning("Optimizer %s not implement.", optimizer_name)
        else:
            logging.info("No config optimizer.")

    def __load_loss(self):
        """Load custom extended loss.

        The loss should be implemented through the extension mechanism.

        Then config in file with:
            "loss": {
                "name": "feddc",
                "params": {}
            }
        """
        if self.__config.get("loss"):
            loss_name = self.__config["loss"].get("name")
            loss_name = "%s_%s" % (self.__runtime, loss_name)
            if loss_name in loss_config:
                loss = self.__load(loss_config[loss_name])
                if loss:
                    self.__config["extenders"].append(loss)
                    logging.info("Load loss %s success.", loss_name)
            else:
                logging.warning("loss %s not implement.", loss_name)
        else:
            logging.info("No config loss.")

    def __is_training_stop(self):
        """Judge whether federate training needs to be terminated early.

        The process can be stopped according to current training state,
        or configured termination condition. Under normal circumstances,
        such as accuracy may be reached early.
        """
        if self.__force_stop:
            return True
        return False

    async def __run_one_round(self, round_id):
        self.__round_id = round_id
        if self.__config.get("block_default"):
            await self.__custom_process()
        else:
            await self.__default_process()

        self.__clean_round()

    async def __default_process(self):
        """Default process is train and evaluate."""
        metrics = None
        result = await self.__run_train_round()
        self.__process_round_result(result)

        if result.status and self.__is_evaluation_conditions():
            metrics = await self.__run_evaluate_round()

        if result.status and self.__is_save_conditions():
            if not metrics:
                metrics = await self.__run_evaluate_round()

            self.__save_ckpts(metrics)

        self.__calculate_statistics(result.status, result.statistics)

    async def __custom_process(self):
        self.__round = CustomRound(self.__config, self.__round_id,
                                   self.__workspace)
        logging.info("Start execute custom round, number %s", self.__round_id)
        result = await self.__round.run()
        self.__calculate_statistics(result.status, result.statistics)

    def __process_round_result(self, result):
        if result.status:
            self.__update_model(result.delta_weights)
            logging.info("Round %s success", self.__round_id)
        else:
            if result.code == ErrorCode.ExtendFailed:
                self.__force_stop = True
            logging.error("Round %s failed, reason: %s", self.__round_id,
                          result.reason)

    async def __run_train_round(self):
        ssa_server = None
        if ("secure_algorithm" in self.__config
                and self.__config["secure_algorithm"]["type"].lower() == "ssa"):
            handle = "%s-%s" % (self.__job_name, self.__round_id)
            ssa_server = create_ssa_server(
                self.__config["secure_algorithm"]["mode"],
                handle=handle,
                min_client_num=self.__config["secure_algorithm"]["threshold"],
                client_num=self.__hyper_params['client_num'],
                use_same_mask=self.__config[
                    "secure_algorithm"]["use_same_mask"],
                wait_aggregate_interval=self.__hyper_params["round_timeout"],
                ssl_key=self.__config['ssl'])
            ssa_server.initialize()

        self.__round = TrainRound(self.__config, self.__round_id,
                                  self.__workspace, self.__fl_model,
                                  ssa_server)
        logging.info("Start execute training round, number %s", self.__round_id)
        return await self.__round.run()

    def __is_evaluation_conditions(self):
        """Judge if satisfy the evaluate conditions."""
        return ((self.__evaluate_interval > 0
                 and self.__round_id % self.__evaluate_interval == 0)
                or self.__round_id == self.__max_rounds)

    async def __run_evaluate_round(self):
        self.__round = EvaluateRound(self.__config, self.__round_id,
                                     self.__workspace, self.__fl_model)
        logging.info("Start evaluating aggregated model.")
        result = await self.__round.run()
        if result.status:
            logging.info("Evaluate result %s", result.metrics)
            # TODO, fl board record metrics
            self.__metrics.append(result.metrics)
            return result.metrics

        logging.warning("Evaluate failed: %s", result.reason)
        return None

    def __save_metrics(self):
        evaluate_metrics = {}
        for metric in self.__metrics:
            for key in metric:
                if key not in evaluate_metrics:
                    evaluate_metrics[key] = []
                evaluate_metrics[key].append(metric[key])

        job_dir = self.__workspace.get_job_dir()
        metrics_file = join(job_dir, "metrics.json")
        with open(metrics_file, "w") as m_f:
            m_f.write(json.dumps(evaluate_metrics, indent=4))
        logging.info("Save training metrics at: %s", metrics_file)

    def __update_model(self, delta_weights):
        self.__fl_model.add_delta_weights(delta_weights)
        logging.info("Update server model success.")

    def __is_save_conditions(self):
        return ((self.__save_interval > 0
                 and self.__round_id % self.__save_interval == 0)
                or self.__round_id == self.__max_rounds)

    def __add_ckpt_info(self, metrics, ckpt_id, ckpt_output_dir, ckpt_file):
        metrics_file = join(ckpt_output_dir,
                            "metrics.json")
        with open(metrics_file, "w") as m_f:
            m_f.write(json.dumps(metrics, indent=4))
        logging.info("Save training metrics at: %s", metrics_file)

        if const.DEPLOYMENT_WAY == "cloud":
            ckpt_file = ckpt_file.lstrip(const.COORDINATOR_WORKSPACE_PATH)

        self.__checkpoints[ckpt_id] = {"path": ckpt_file,
                                       "accuracy": metrics.get("accuracy")}

    def __save_ckpts(self, metrics=None):
        ckpt_dir_name, ckpt_out_path = self.__workspace.create_ckpt_dir(
            self.__next_ckpt_id)

        ckpt_filename = self.__workspace.get_runtime_file_by(Files.Checkpoint,
                                                             self.__runtime,
                                                             self.__round_id)
        ckpt_file = join(ckpt_out_path, ckpt_filename)

        self.__fl_model.save_model(ckpt_file)

        if metrics and metrics.get("accuracy"):
            self.__add_ckpt_info(metrics, ckpt_dir_name,
                                 ckpt_out_path, ckpt_file)

        self.__next_ckpt_id += 1
        logging.info("Saving checkpoint to %s success", ckpt_file)

    async def msg_mux(self, msg_type, msg):
        """Dispatch the message from clients to round."""
        msg_dispatch = {Message.TRAIN: self.__process_train_reply,
                        Message.EVALUATE: self.__process_evaluate_reply,
                        Message.STOP: self.__process_stop_cmd}

        await msg_dispatch[msg_type](msg)

    async def __process_train_reply(self, msg):
        self.__assert_msg_belongings(msg[0])
        await self.__round.process(msg)

    async def __process_evaluate_reply(self, msg):
        self.__assert_msg_belongings(msg[0])
        await self.__round.process(msg)

    async def __process_stop_cmd(self, msg):
        del msg
        self.__force_stop = True
        self.__state = State.STOPPING
        await self.__round.stop()

    def __assert_msg_belongings(self, msg):
        """Assert upload message belong to current job and round.

        Only the message has the same job name and round id will be processed,
        that means this message belong to current job and with the right round.
        Otherwise it will be refused.
        """
        if msg.metadata.job_name != self.__job_name:
            logging.error("Updates is not belong to current job")
            raise ValueError("Msg not matched!")

        if msg.metadata.round != self.__round_id:
            logging.error("Updates is not belong to current round")
            raise ValueError("Msg not matched!")

    def __calculate_statistics(self, status, statistics):
        if status:
            self.__stats.increase_success()
        else:
            self.__stats.increase_failed()

        self.__stats.calculate_progress(self.__round_id, self.__max_rounds)
        self.__stats.increase_spend_time(statistics.spend_time)

    def get_statistics(self):
        """Return the statistics of the federated job execution."""
        return self.__stats

    def finish(self):
        """Do finish job after the training.

        Typically, delete the useless temporary files and directories.
        """
        self.__save_metrics()
        tmp_dir = self.__workspace.get_tmp_dir()
        delete(tmp_dir)

    def __clean_round(self):
        """Do clean job after the each round.

        Typically, delete the round dir(saving temporary intermediate file).
        """
        round_dir = self.__workspace.get_round_dir(self.__round_id)
        delete(round_dir)
