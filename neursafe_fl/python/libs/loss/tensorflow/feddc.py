#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
# pylint:disable=too-many-instance-attributes, too-many-arguments
"""
FedDC for Tensorflow.
"""
import logging
import math
import os

import numpy as np
import tensorflow as tf
from tensorflow.keras.losses import Loss
import tensorflow.keras.backend as K

from neursafe_fl.python.sdk.custom import get_file, put_file
from neursafe_fl.python.sdk.utils import get_round_num, get_worker_id


H_I_FILE = os.getenv("H_I_FILE", "/tmp/local_h_i_%s.npy")
G_I_FILE = os.getenv("G_I_FILE", "/tmp/local_g_i_%s.npy")

GLOBAL_G_FILE = "global_variates.npy"


def _get_worker_id_prefix():
    worker_id = get_worker_id()
    worker_id_splited = worker_id.split("-")
    worker_id_prefix = "-".join(worker_id_splited[:-3]) + "-"
    return worker_id_prefix


def _read_data(file_name, np_array=True):
    if np_array:
        return np.load(file_name, allow_pickle=True)

    return tf.convert_to_tensor(np.load(file_name, allow_pickle=True))


def _write_data(file_name, data):
    np.save(file_name, data)


def _set_model_params(model, params):
    new_params = []
    idx = 0
    for param in model.get_weights():
        length = len(param.reshape(-1))
        new_params.append(
            np.array(params[idx:idx + length].reshape(param.shape)))
        idx += length

    model.set_weights(new_params)
    return model


def _flatten_model_params(model, parmas_num=None):
    if parmas_num is None:
        parmas_num = 0
        for param in model.get_weights():
            parmas_num += len(param.reshape(-1))

    param_mat = np.zeros(parmas_num).astype('float32')
    idx = 0
    for param in model.get_weights():
        temp = param.reshape(-1)
        param_mat[idx:idx + len(temp)] = temp
        idx += len(temp)
    return np.copy(param_mat)


class FeddcLoss(Loss):
    """The FedDC Loss.

    FeddcLoss is used for data heterogeneity in federated learning. when use
    fedDC in tensorflow, you shoud like this:
    >> loss = nsfl.create_loss(model, sample_num=1000, batch_size=32,
                               lr=0.001, epoch=5, alpha=0.01)
    >> model.compile(optimizer=SGD(lr=0.001),
                      loss=loss,
                      metrics=["accuracy"],
                      run_eagerly=True)
    Note, run_eagerly must set True, because tensor should be run as
    EagerTensor in FeddcLoss.call.

    Args:
        model: The model will be using to train. and it already loaded
               init weights from server.
        origin_loss_func: Base loss function used for train. Default is
                          categorical_crossentropy.
        sample_num: The number of samples used in this round when training
                    the local model.
        batch_size: The batch size used when training the local model.
        lr: Local training learning rate.
        epoch: The epoch used when training the local model.
        alpha: The hyper-parameter that controls the weight of R, The
               recommended setting value is 0.1/0.01/0.005.
        print_loss: Printing detail loss per call.
    """
    _instance = None

    @classmethod
    def get_instance(cls, *args, **kwargs):
        """Get feddc loss instance.
        """
        if not cls._instance:
            cls._instance = FeddcLoss(*args, **kwargs)
        return cls._instance

    def __init__(self, model,
                 origin_loss_func=K.categorical_crossentropy,
                 sample_num=1, batch_size=32, lr=0.01, epoch=1, alpha=0.01,
                 print_loss=20):
        super().__init__()
        self._model = model
        self._origin_loss_func = origin_loss_func
        self._global_weights = tf.convert_to_tensor(
            _flatten_model_params(model))
        self._param_num = len(self._global_weights)
        self._alpha = alpha / 2
        self._call_time = 0
        self._print_loss_per_call = print_loss

        self._param_a = 1 / (math.ceil(sample_num / batch_size) * epoch) / lr

        self._task_id_prefix = _get_worker_id_prefix()
        round_num = get_round_num()
        if round_num == 1:
            self._init_params()
        else:
            try:
                self._h_i = _read_data(H_I_FILE % self._task_id_prefix,
                                       np_array=False)
                self._g_i = _read_data(G_I_FILE % self._task_id_prefix,
                                       np_array=True)
                self._g = get_file(GLOBAL_G_FILE,
                                   dserialize_func=np.load)
            except FileNotFoundError:
                # If the client is partially involved in the FL, the initial
                # value needs to be given when not find the param file.
                self._init_params()

        self._g_diff = tf.convert_to_tensor(self._g - self._g_i)
        self._h_diff = self._global_weights - self._h_i

    def _init_params(self):
        n_par = len(self._global_weights)

        self._g_i = np.zeros(n_par).astype('float32')
        self._g = np.zeros(n_par).astype('float32')
        self._h_i = tf.zeros(n_par)

    def call(self, y_true, y_pred):
        loss_f_i = self._origin_loss_func(y_true, y_pred)
        loss_f_i = K.mean(loss_f_i)

        local_parameter = tf.convert_to_tensor(
            _flatten_model_params(self._model, self._param_num))

        # R
        temp = local_parameter - self._h_diff
        loss_cp = self._alpha * K.sum(temp * temp)
        # G
        loss_cg = K.sum(local_parameter * self._g_diff)

        loss = loss_f_i + loss_cp + loss_cg
        if (self._print_loss_per_call
                and self._call_time % self._print_loss_per_call == 0):
            logging.info("origin: %s, R: %s, G: %s, total: %s.",
                         loss_f_i, loss_cp, loss_cg, loss)
        self._call_time += 1
        return loss

    def update_and_commit_param(self, commiting_model):
        """Update g_i and h_i, and commit delta g_i.
        """
        trained_params = _flatten_model_params(commiting_model,
                                               self._param_num)
        # calculate delta weights
        delta_weights = trained_params - self._global_weights.numpy()

        # g_i^+=g_i-g+1/(K*\eta)*(-\Delta\theta_i)
        new_g_i = self._g_i - self._g - self._param_a * delta_weights

        # \Delta g_i=g_i^+-g_i
        delta_g_i = new_g_i - self._g_i

        # h_i=h_i+\Delta\theta_i
        new_h_i = self._h_i.numpy() + delta_weights

        # save new_g_i and new_h_i
        _write_data(G_I_FILE % self._task_id_prefix, new_g_i)
        _write_data(H_I_FILE % self._task_id_prefix, new_h_i)

        # upload the delta g_i
        put_file("delta_control_variates.npy", delta_g_i,
                 serialize_func=np.save)
        put_file("h_i.npy", new_h_i, serialize_func=np.save)
