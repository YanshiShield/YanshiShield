#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=missing-function-docstring, too-many-arguments
"""Trainer UnitTest."""
import unittest
import asyncio
import mock

from neursafe_fl.python.coordinator.trainer import Trainer, Message
from neursafe_fl.python.coordinator.common.types import RoundResult, Statistics
from neursafe_fl.proto.message_pb2 import TaskResult, Metadata


def _construct_result():
    stats = Statistics()
    stats.success = 1
    stats.failed = 1
    stats.spend_time = 10
    stats.progress = 0.99
    result = RoundResult()
    result.metrics = {}
    result.status = False
    result.delta_weights = None
    result.statistics = stats
    return result


def _construct_message(job_name):
    metadata = Metadata(job_name=job_name,
                        round=1)
    task_result = TaskResult(metadata=metadata)
    return task_result


async def fake_success_run():
    result = _construct_result()
    result.status = True
    return result


async def fake_failed_run():
    result = _construct_result()
    result.status = False
    return result


async def fake_process(msg):
    del msg
    return


class TestTrainer(unittest.TestCase):
    """Test class."""

    def test_should_init_trainer_object_success(self):
        config = trainer_config()
        Trainer(config)

    def test_should_raise_exception_when_config_not_correct(self):
        config = trainer_config()
        del config["runtime"]
        with self.assertRaises(KeyError):
            Trainer(config)

        config = trainer_config()
        del config["model_path"]
        with self.assertRaises(KeyError):
            Trainer(config)

    @mock.patch("neursafe_fl.python.coordinator.rounds.train_round.TrainRound.run")
    @mock.patch("neursafe_fl.python.coordinator.rounds.evaluate_round.EvaluateRound.run")
    @mock.patch("neursafe_fl.python.coordinator.fl_model.FlModel.add_delta_weights")
    @mock.patch("neursafe_fl.python.coordinator.fl_model.FlModel.save_model")
    @mock.patch("neursafe_fl.python.coordinator.fl_model.FlModel.load")
    def test_should_trainer_run_default_process_success(self, load, save, add,
                                                        e_run, t_run):
        load.return_value = None
        save.return_value = None
        add.return_value = None
        e_run.side_effect = fake_success_run
        t_run.side_effect = fake_success_run
        config = trainer_config()
        trainer = Trainer(config)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(trainer.start())

    @mock.patch("neursafe_fl.python.coordinator.rounds.train_round.TrainRound.run")
    @mock.patch("neursafe_fl.python.coordinator.fl_model.FlModel.load")
    def test_should_trainer_run_train_round_failed(self, load, run):
        load.return_value = None
        run.side_effect = fake_failed_run
        config = trainer_config()
        trainer = Trainer(config)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(trainer.start())

    @mock.patch("neursafe_fl.python.coordinator.rounds.custom_round.CustomRound.run")
    @mock.patch("neursafe_fl.python.coordinator.fl_model.FlModel.load")
    def test_should_trainer_run_custom_process_success(self, load, run):
        load.return_value = None
        run.side_effect = fake_success_run
        config = trainer_config()
        config["block_default"] = True
        trainer = Trainer(config)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(trainer.start())

    @mock.patch("neursafe_fl.python.coordinator.rounds.train_round.TrainRound.run")
    @mock.patch("neursafe_fl.python.coordinator.rounds.train_round.TrainRound.process")
    @mock.patch("neursafe_fl.python.coordinator.fl_model.FlModel.load")
    def test_should_trainer_dispatch_message_success(self, load, process, run):
        load.return_value = None
        process.side_effect = fake_process
        run.side_effect = fake_failed_run

        config = trainer_config()
        trainer = Trainer(config)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(trainer.start())

        # construct proto message
        message = _construct_message(config["job_name"])
        loop.run_until_complete(trainer.msg_mux(Message.TRAIN, (message, None)))

    @mock.patch("neursafe_fl.python.coordinator.rounds.train_round.TrainRound.run")
    @mock.patch("neursafe_fl.python.coordinator.rounds.train_round.TrainRound.process")
    @mock.patch("neursafe_fl.python.coordinator.fl_model.FlModel.load")
    def test_should_trainer_raise_exception_when_dispatch_wrong_msg_type(
            self, load, process, run):
        load.return_value = None
        process.side_effect = fake_process
        run.side_effect = fake_failed_run

        config = trainer_config()
        trainer = Trainer(config)
        loop = asyncio.get_event_loop()

        message = _construct_message(config["job_name"])
        with self.assertRaises(KeyError):
            loop.run_until_complete(trainer.msg_mux("error", (message, None)))

    @mock.patch("neursafe_fl.python.coordinator.rounds.train_round.TrainRound.run")
    @mock.patch("neursafe_fl.python.coordinator.rounds.train_round.TrainRound.process")
    @mock.patch("neursafe_fl.python.coordinator.fl_model.FlModel.load")
    def test_should_trainer_raise_exception_when_msg_not_match_this_round(
            self, load, process, run):
        load.return_value = None
        process.side_effect = fake_process
        run.side_effect = fake_failed_run

        config = trainer_config()
        trainer = Trainer(config)
        loop = asyncio.get_event_loop()

        message = _construct_message(config["job_name"])
        with self.assertRaises(ValueError):
            loop.run_until_complete(trainer.msg_mux(Message.TRAIN,
                                                    (message, None)))

    @mock.patch("neursafe_fl.python.coordinator.fl_model.FlModel.load")
    def test_should_trainer_start_failed_when_load_model_failed(self, load):
        def fake_load():
            raise RuntimeError
        load.side_effect = fake_load
        config = trainer_config()
        trainer = Trainer(config)

        with self.assertRaises(RuntimeError):
            loop = asyncio.get_event_loop()
            loop.run_until_complete(trainer.start())


def trainer_config():
    return {
        "job_name": "test",
        "description": "test case",
        "host": "0.0.0.0",
        "port": 9090,
        "clients": "0.0.0.1:34567",
        "model_path": "/tmp/init_model.h5",
        "runtime": "tensorflow",
        "task_entry": "flower",
        "output": "/tmp",
        "hyper_parameters": {
            "max_round_num": 1,
            "client_num": 1,
            "threshold_client_num": 1,
            "evaluate_interval": 0,
            "save_interval": 0
        }
    }


if __name__ == "__main__":
    unittest.main()
