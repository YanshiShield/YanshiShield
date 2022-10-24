#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
# pylint: disable=invalid-name, global-statement
"""FL SDk core function.
"""

import os
from absl import logging

import neursafe_fl.python.sdk.utils as utils
import neursafe_fl.python.sdk.report as report
import neursafe_fl.python.client.workspace.delta_weights as weights
from neursafe_fl.python.utils.file_io import read_json_file
from neursafe_fl.python.runtime.runtime_factory import RuntimeFactory
from neursafe_fl.python.libs.compression.factory import create_compression

fl_model = None


def load_weights(model):
    """Load weights from server into model.

    Args:
        model: The model will be loaded weights.
    """
    task_workspace = utils.get_task_workspace()
    runtime = utils.get_runtime()

    global fl_model
    fl_model = weights.load_init_weights(model, runtime, task_workspace)


def __is_chief_worker():
    if os.getenv("WORKER_INDEX", "0") == "0":
        return True

    logging.debug("No chief worker.")
    return False


def _calc_delta_weights(model):
    delta_weights = weights.calculate_delta_weights(model,
                                                    utils.get_runtime())
    return delta_weights


def _protect_weights(weights_, metrics):
    security_algorithm = utils.create_security_algorithm()

    if security_algorithm:
        protected_weights = utils.do_function_sync(
            security_algorithm.protect_weights, weights_,
            sample_num=metrics.get('sample_num', 1))

        return protected_weights

    return weights_


def _compress_weights(weights_):
    compression_algorithm = utils.get_compression_algorithm()

    if compression_algorithm:
        runtime = utils.get_runtime()
        compression = create_compression(compression_algorithm["type"],
                                         **compression_algorithm)
        weight_converter = RuntimeFactory.create_weights_converter(runtime)

        return weight_converter.encode(weights_, compression)

    return weights_


def _commit_trained_results(metrics, model, optimizer=None):
    def do_optional_works():
        global fl_model
        fl_model.set_raw_model(model)

        if os.getenv(utils.TASK_OPTIMIZER) == "scaffold" and optimizer:
            optimizer.update(fl_model)

    if __is_chief_worker():
        # STEP 1: Do optional works
        do_optional_works()

        # STEP 2: Calculate delta weights.
        delta_weights = _calc_delta_weights(fl_model)

        # STEP 3: Compress delta weights if needed
        delta_weights = _compress_weights(delta_weights)

        # STEP 4: Protect delta weights if needed
        delta_weights = _protect_weights(delta_weights, metrics)

        # STEP 5: Report to coordinator.
        report.submit(metrics, delta_weights)


def _commit_evaluated_results(metrics):
    # Report to coordinator
    report.submit(metrics)


def commit(metrics, trained_model=None, optimizer=None):
    """Commit trained weights to framework, and the framework will
    calculate delta weights and send it to server.

    Args:
        metrics: A dictionary stored the metrics data after train or evaluate,
            the key include:
                sample_num int32,
                spend_time int32,
                loss float,
                accuracy float,
                precision float,
                recall_rate float,
            all is optional.
        trained_model: trained model.
        optimizer: the optimizer instance used in training.
    """
    if trained_model:
        _commit_trained_results(metrics, trained_model, optimizer=optimizer)
    else:
        _commit_evaluated_results(metrics)


def get_dataset_path(name):
    """Get the path of the dataset by the dataset key.

    Args:
        name: Get the path of a dataset based on this name.
    """
    return read_json_file(utils.get_datasets())[name]
