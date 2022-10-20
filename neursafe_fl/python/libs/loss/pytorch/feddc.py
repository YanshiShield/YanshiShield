#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-many-instance-attributes, too-many-arguments, no-member
# pylint:disable=not-callable
"""
FedDC for pytorch.
"""
import copy
import logging
import math
import os

import torch
from torch.nn.modules.loss import _WeightedLoss, CrossEntropyLoss
import numpy as np

from neursafe_fl.python.sdk.custom import get_file, put_file
from neursafe_fl.python.sdk.utils import get_worker_id, get_round_num


H_I_FILE = os.getenv("H_I_FILE", "/tmp/nsfl_feddc_local_h_i_%s.pt")
G_I_FILE = os.getenv("G_I_FILE", "/tmp/nsfl_feddc_local_g_i_%s.pt")

GLOBAL_G_FILE = "global_variates.pt"


def _get_worker_id_prefix():
    worker_id = get_worker_id()
    worker_id_splited = worker_id.split("-")
    worker_id_prefix = "-".join(worker_id_splited[:-3]) + "-"
    return worker_id_prefix


def _read_data(file_name, np_array=True):
    if np_array:
        return torch.load(file_name).detach().numpy()
    return torch.load(file_name)


def _write_data(file_name, data):
    tensor_data = torch.from_numpy(data)
    torch.save(tensor_data, file_name)


def _set_model_params(model, params, device="cpu"):
    dict_param = copy.deepcopy(dict(model.named_parameters()))
    idx = 0
    for name, param in model.named_parameters():
        weights = param.data
        length = len(weights.reshape(-1))
        dict_param[name].data.copy_(torch.tensor(
            params[idx:idx + length].reshape(weights.shape)).to(device))
        idx += length

    model.load_state_dict(dict_param)
    return model


def _flatten_model_params(model, parmas_num=None):
    if parmas_num is None:
        parmas_num = 0
        for _, param in model.named_parameters():
            parmas_num += len(param.data.reshape(-1))

    param_mat = np.zeros(parmas_num).astype('float32')
    idx = 0
    for _, param in model.named_parameters():
        temp = param.data.cpu().numpy().reshape(-1)
        param_mat[idx:idx + len(temp)] = temp
        idx += len(temp)
    return np.copy(param_mat)


class FeddcLoss(_WeightedLoss):
    """The FedDC Loss.

    FeddcLoss is used for data heterogeneity in federated learning. when use
    fedDC in pytorch, you shoud like this:
    >> loss = nsfl.create_loss(model, sample_num=1000, batch_size=32,
                               lr=0.001, epoch=5, alpha=0.01)
    >> loss(out, target)

    Args:
        train_model: The model will be using to train. and it already loaded
                     init weights from server.
        origin_loss_func: Base loss function used for train. Default is
                          CrossEntropyLoss.
        sample_num: The number of samples used in this round when training
                    the local model.
        batch_size: The batch size used when training the local model.
        lr: Local training learning rate.
        epoch: The epoch used when training the local model.
        alpha: The hyper-parameter that controls the weight of R, The
               recommended setting value is 0.1/0.01/0.005.
        device: Use cpu or gpu when run training.
        print_loss_per_forward: Printing detail loss per forward.
    """
    _instance = None

    @classmethod
    def get_instance(cls, *args, **kwargs):
        """Get feddc loss instance.
        """
        if not cls._instance:
            cls._instance = FeddcLoss(*args, **kwargs)
        return cls._instance

    def __init__(self, train_model,
                 origin_loss_func=CrossEntropyLoss(reduction='sum'),
                 sample_num=1, batch_size=32, lr=0.01, epoch=1, alpha=0.01,
                 device="cpu", print_loss_per_forward=20):
        super().__init__()
        self._train_model = train_model.to(device)
        self._origin_loss_func = origin_loss_func.to(device)
        self._global_weights = torch.tensor(_flatten_model_params(train_model),
                                            dtype=torch.float32, device=device)
        self._param_num = len(self._global_weights)
        self._alpha = alpha / 2
        self._device = device
        self._forward_time = 0
        self._print_loss_per_forward = print_loss_per_forward

        self._param_a = 1 / (math.ceil(sample_num / batch_size) * epoch) / lr

        self.task_id_prefix = _get_worker_id_prefix()
        round_num = get_round_num()
        if round_num == 1:
            n_par = len(self._global_weights)

            self._g_i = np.zeros(n_par).astype('float32')
            self._g = np.zeros(n_par).astype('float32')
            self._h_i = torch.zeros(n_par, dtype=torch.float32).to(device)
        else:
            self._h_i = _read_data(H_I_FILE % self.task_id_prefix,
                                   np_array=False).to(device)
            self._g_i = _read_data(G_I_FILE % self.task_id_prefix,
                                   np_array=True)
            self._g = torch.stack(
                get_file(GLOBAL_G_FILE,
                         dserialize_func=torch.load)).detach().numpy()

        self._g_diff = torch.tensor(self._g - self._g_i,
                                    dtype=torch.float32, device=device)
        self._h_diff = self._global_weights - self._h_i

    def forward(self, outputs, target):
        """Forward.
        """
        loss_f_i = self._origin_loss_func(outputs, target.reshape(-1))
        loss_f_i = loss_f_i / list(target.size())[0]

        local_parameter = None
        for param in self._train_model.parameters():
            if not isinstance(local_parameter, torch.Tensor):
                local_parameter = param.reshape(-1)
            else:
                local_parameter = torch.cat((local_parameter,
                                             param.reshape(-1)), 0)

        # R
        temp = local_parameter - self._h_diff
        loss_cp = self._alpha * torch.sum(temp * temp)
        # G
        loss_cg = torch.sum(local_parameter * self._g_diff)

        loss = loss_f_i + loss_cp + loss_cg
        if (self._print_loss_per_forward
                and self._forward_time % self._print_loss_per_forward == 0):
            print(loss_f_i)
            logging.info("origin: %s, R: %s, G: %s, total: %s.",
                         loss_f_i, loss_cp, loss_cg, loss)
        self._forward_time += 1
        return loss

    def update_and_commit_param(self, commiting_model):
        """Update g_i and h_i, and commit delta g_i.
        """
        trained_params = _flatten_model_params(commiting_model,
                                               self._param_num)
        init_params = self._global_weights.cpu().detach().numpy()
        # calculate delta weights
        delta_weights = trained_params - init_params

        # g_i^+=g_i-g+1/(K*\eta)*(-\Delta\theta_i)
        new_g_i = self._g_i - self._g - self._param_a * delta_weights

        # \Delta g_i=g_i^+-g_i
        delta_g_i = new_g_i - self._g_i

        # h_i=h_i+\Delta\theta_i
        h_i = self._h_i.cpu().detach().numpy()
        new_h_i = h_i + delta_weights

        # update local weights
        new_trained_params = trained_params + new_h_i
        _set_model_params(commiting_model, new_trained_params)

        # save new_g_i and new_h_i
        _write_data(G_I_FILE % self.task_id_prefix, new_g_i)
        _write_data(H_I_FILE % self.task_id_prefix, new_h_i)

        # upload the delta g_i
        def serialize(file_obj, content):
            content = torch.from_numpy(content)
            torch.save(content, file_obj)
        put_file("delta_control_variates.pt", delta_g_i,
                 serialize_func=serialize)
