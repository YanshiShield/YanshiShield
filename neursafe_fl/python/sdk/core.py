#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""FL SDk core function.
"""

import os
from absl import logging

from neursafe_fl.python.client.workspace.delta_weights import \
    load_init_weights, save_trained_weights, save_trained_model
from neursafe_fl.python.client.workspace.metrics import write_metrics
from neursafe_fl.python.runtime.runtime_factory import Runtime
from neursafe_fl.python.sdk.utils import get_task_workspace, get_runtime, \
    get_datasets
from neursafe_fl.python.utils.file_io import read_json_file


def load_weights(model):
    """Load weights from server into model.

    Args:
        model: The model will be loaded weights.
    """
    task_workspace = get_task_workspace()
    runtime = get_runtime()
    load_init_weights(model, runtime, task_workspace)


def __is_chief_worker():
    if os.getenv("WORKER_INDEX", "0") == "0":
        return True

    logging.debug("No chief worker.")
    return False


def commit_weights(model, optimizer=None):
    """Commit trained weights to framework, and the framework will
    calculate delta weights and send it to server.

    Args:
        model: Will commit the weights in model to framework.
        optimizer: the optimizer instance used in training.
    """
    if __is_chief_worker():
        task_workspace = get_task_workspace()
        runtime = get_runtime()
        if runtime == Runtime.PYTORCH.value:
            save_trained_weights(model, runtime, task_workspace)
        else:
            save_trained_model(model, runtime, task_workspace)

        if os.getenv("OPTIMIZER_NAME") == "scaffold" and optimizer:
            optimizer.update(model)


def commit_metrics(metrics):
    """Commit metrics to server.

    Training or evaluating metrics would be committed to framework, and the
    framework will send it to server.

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
    """
    if __is_chief_worker():
        task_workspace = get_task_workspace()
        write_metrics(task_workspace, metrics)


def get_dataset_path(name):
    """Get the path of the dataset by the dataset key.

    Args:
        name: A index name of the dataset you want to obtain in the dataset
            mapping configuration file.
    """
    return read_json_file(get_datasets())[name]
