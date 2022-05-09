#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Used to save and read the model/weights under the task workspace,
including the initial weights from server and the result model/weights
after task finished.
"""

import os
from absl import logging
from neursafe_fl.python.runtime.runtime_factory import Runtime, RuntimeFactory


_INIT_WEIGHTS_FILE_NAME = 'init_weights'
_TRAINED_MODEL_FILE_NAME = 'trained_model'
_TRAINED_WEIGHTS_FILE_NAME = 'trained_weights'
_DELTA_WEIGHT_FILE_NAME = 'delta_weights'

_SUFFIX_MAP = {
    'tensorflow': '.h5',
    'pytorch': '.pth',
    Runtime.TENSORFLOW: '.h5',
    Runtime.PYTORCH: '.pth'
}


def get_init_weight_file_name(runtime, workspace):
    """Get init weight file name in task workspace.

    Args:
        runtime: One of enum(tensorflow, pytorch).
        workspace: Task's workspace.

    Return:
        The init weight file path, which saved init weights from server.
    """
    return os.path.join(workspace,
                        _INIT_WEIGHTS_FILE_NAME + _SUFFIX_MAP[runtime])


def get_trained_weights_file_name(runtime, workspace):
    """Get trained weights file name in task workspace.

    Used in pytorch runtime. In pytorch, the client needs to know the trained
    weights and init weights from server to calculate delta weights. Because
    in pytorch, the client cannot load the trained model without know the model
    class and the client is hard to know the model class.

    Args:
        runtime: One of enum(tensorflow, pytorch).
        workspace: Task's workspace.

    Return:
        The trained weight file path, which saved trained weights
        after task finish.
    """
    return os.path.join(workspace,
                        _TRAINED_WEIGHTS_FILE_NAME + _SUFFIX_MAP[runtime])


def get_trained_model_file_name(runtime, workspace):
    """Get trained model file in task workspace.

    Used tensorflow runtime. In tensorflow, the client needs to know the trained
    model(include trained weights) and init weights from server to calculate
    delta weights. Because the client cannot load the trained weights without
    know the model in tensorflow.

    Args:
        runtime: One of enum(tensorflow, pytorch).
        workspace: Task's workspace.

    Return:
        The trained model file path, which saved trained model
        after task finish.
    """
    return os.path.join(workspace,
                        _TRAINED_MODEL_FILE_NAME + _SUFFIX_MAP[runtime])


def get_delta_weights_file_name(runtime, workspace):
    """Get delta weights file in task workspace.

    Args:
        runtime: One of enum(tensorflow, pytorch).
        workspace: Task's workspace.

    Return:
        The delta weights file path, which will be saved delta weights
        after client calculate delta weights.
    """
    return os.path.join(workspace,
                        _DELTA_WEIGHT_FILE_NAME + _SUFFIX_MAP[runtime])


def load_init_weights(model, runtime, workspace):
    """Load init weights into model.

    Args:
        model: The weights will be loaded into model.
        runtime: One of enum(tensorflow, pytorch).
        workspace: Task's workspace.

    Return:
        The loaded weights.
    """
    weights_file_name = get_init_weight_file_name(runtime, workspace)
    fl_model = RuntimeFactory.create_model(runtime, model=model)
    return fl_model.load(weights_file_name, load_type='weights',
                         return_type='weights')


def save_trained_weights(model, runtime, workspace):
    """Save trained weights.

    Because in pytorch, the client cannot load the trained model without know
    the model class and the client is hard to know the model class. so after
    task finished, just need save trained weights.

    Args:
        model: The weights in model will be saved.
        runtime: One of enum(tensorflow, pytorch).
        workspace: Task's workspace.
    """
    trained_weights_file_name = get_trained_weights_file_name(runtime,
                                                              workspace)
    fl_model = RuntimeFactory.create_model(runtime)
    fl_model.save(model, trained_weights_file_name)


def _has_trained_weights(runtime, workspace):
    weight_path = get_trained_weights_file_name(runtime, workspace)
    return os.path.exists(weight_path)


def save_trained_model(model, runtime, workspace):
    """Save trained model to task workspace.

    Because in tensorflow, the client cannot load the trained weights without
    know the model. So after task finished, should save trained model.

    Args:
        model: The model will be saved.
        runtime: One of enum(tensorflow, pytorch).
        workspace: Task's workspace.
    """
    model_path = get_trained_model_file_name(runtime, workspace)
    fl_model = RuntimeFactory.create_model(runtime, model=model)
    fl_model.save(model, model_path, save_type='model')


def _has_trained_model(runtime, workspace):
    model_path = get_trained_model_file_name(runtime, workspace)
    return os.path.exists(model_path)


def has_trained_weights_result(runtime, workspace):
    """Whether has trained weights result.

    Check whether task has saved trained weights in pytorch, and
    check whether task has saved trained model in tensorflow.

    Args:
        runtime: One of enum(tensorflow, pytorch).
        workspace: Task's workspace.

    Return:
        if trained weights file exist in pytorch or trained model exist
        in tensorflow, return True, else False.
    """
    if runtime == Runtime.PYTORCH.value:
        if _has_trained_weights(runtime, workspace):
            return True
    else:
        if _has_trained_model(runtime, workspace):
            return True
    logging.warning("can't find result in workspace after the task finished, "
                    "maybe you should use save_trained_weights or "
                    "save_trained_model in SDK for your script, %s",
                    workspace)
    return False


def save_delta_weights(fl_model, weights, runtime, workspace):
    """Save delta weights to task workspace.

    Args:
        fl_model:generated by runtime, used to load weights.
        weights: The weights will be saved.
        runtime: One of enum(tensorflow, pytorch).
        workspace: Task's workspace.

    Return:
        A file path saved delta weights.
    """
    file_name = get_delta_weights_file_name(runtime, workspace)
    fl_model.save(weights, file_name, save_type='weights')

    return file_name


def calculate_delta_weights(fl_model, runtime, workspace):
    """Calculate delta weights after task finish.

    In tensorflow runtime, used trained_model and init_weights to calculate
    delta weights. In pytorch runtime, used trained_weights and init_weights
    to calculate delta weights.

    Args:
        fl_model:generated by runtime, used to load weights.
        runtime: One of enum(tensorflow, pytorch).
        workspace: Task's workspace.

    Return:
        The delta weights. In pytorch, is a OrderedDict, In tensorflow, is list.
    """
    if runtime == Runtime.PYTORCH.value:
        trained_result = get_trained_weights_file_name(runtime, workspace)
    else:
        trained_result = get_trained_model_file_name(runtime, workspace)

    trained_weights = __load_trained_weights(fl_model, trained_result)
    init_weights = __load_init_weights(fl_model, runtime, workspace)

    return __cal_delta_weights(runtime, trained_weights, init_weights)


def __load_trained_weights(fl_model, trained_result):
    return fl_model.load(
        trained_result, load_type='model', return_type='weights')


def __load_init_weights(fl_model, runtime, workspace):
    return fl_model.load(
        get_init_weight_file_name(runtime, workspace), load_type='weights',
        return_type='weights')


def __cal_delta_weights(runtime, trained_weights, init_weights):
    calculator = RuntimeFactory.create_weights_calculator(runtime)
    return calculator.subtract(trained_weights, init_weights)
