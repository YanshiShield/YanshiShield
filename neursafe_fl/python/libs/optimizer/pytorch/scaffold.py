#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint: disable=no-member, invalid-name, no-name-in-module, not-callable
# pylint: disable=too-many-locals, too-many-arguments
"""SCAFFOLD Optimizer algorithm.
"""
import os
import math
import itertools
import torch
from absl import logging
from torch.optim.optimizer import Optimizer
from neursafe_fl.python.sdk.custom import get_file, put_file
from neursafe_fl.python.sdk.core import load_weights

# The local control_variates file path
local_control_variates_path = os.getenv("CONTROL_VARIATES",
                                        "/tmp/local_variates.pt")

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


def get_init_variates(model_params):
    """Get the init variates for scaffold.
    """
    local_c, server_c = [], []
    for p in model_params:
        if p.requires_grad:
            local_c.append(torch.zeros_like(p.data))
            server_c.append(torch.zeros_like(p.data))
    if os.path.exists(local_control_variates_path):
        local_c = torch.load(local_control_variates_path)

    global_control_variates_name = "global_variates.pt"
    try:
        server_c = get_file(global_control_variates_name,
                            dserialize_func=torch.load)
    except (OSError, KeyError):
        logging.warning("Server control variates not found.")

    return server_c, local_c


def update_local_variates(trained_params, zero_params, server_params,
                          server_controls, local_controls, sample_num,
                          batch_size, lr):
    """Update the local control variates and upload the delta control variates.
    """
    delta_model = []
    new_local_controls = []
    delta_controls = []
    for p in zero_params:
        delta_model.append(torch.zeros_like(p.data, device=device))
        new_local_controls.append(torch.zeros_like(p.data, device=device))
        delta_controls.append(torch.zeros_like(p.data, device=device))

    # get model difference (delta model)
    for local, server, delta in zip(trained_params, server_params,
                                    delta_model):
        local = local.to(device)
        server = server.to(device)
        delta = delta.to(device)
        delta.data = local.data.detach() - server.data.detach()

    # get client new control variates
    for server_control, local_control, delta, new_control in zip(
            server_controls, local_controls, delta_model, new_local_controls):
        server_control = server_control.to(device)
        local_control = local_control.to(device)
        delta = delta.to(device)
        new_control = new_control.to(device)
        a = 1 / (math.ceil(sample_num / batch_size) * lr)
        new_control.data = local_control.data - server_control.\
            data - delta.data * a

    # get controls differences (delta control)
    for old_control, new_control, delta in zip(local_controls,
                                               new_local_controls,
                                               delta_controls):
        old_control = old_control.to(device)
        new_control = new_control.to(device)
        delta = delta.to(device)
        delta.data = new_control.data - old_control.data
        old_control.data = new_control.data

    # save the new local control to local path
    torch.save(new_local_controls, local_control_variates_path)

    # upload the delta control
    def serialize(file_obj, content):
        torch.save(content, file_obj)
    put_file("delta_control_variates.pt", delta_controls,
             serialize_func=serialize)


class Scaffold(Optimizer):
    """Scaffold optimizer.
    """

    def __init__(self, model_params=None, lr=0.01, batch_size=None,
                 sample_num=None, **kwargs):
        params_1, params_2 = itertools.tee(model_params, 2)
        defaults = dict(lr=lr, weight_decay=kwargs.get("weight_decay", 0.004))
        super().__init__(params_1, defaults)

        self.batch_size = batch_size
        self.sample_num = sample_num
        self.lr = lr
        self.server_controls, self.local_controls = \
            get_init_variates(params_2)

    def step(self, closure=None):
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()

        for group in self.param_groups:
            for p, c, ci in zip(group['params'], self.server_controls,
                                self.local_controls):
                p = p.to(device)
                c = c.to(device)
                ci = ci.to(device)
                if p.grad is None:
                    continue

                d_p = p.grad.data + c.data - ci.data
                p.data = p.data - d_p.data * group['lr']

        return loss

    def update(self, model):
        """Update the control variates of scaffold
        """
        if isinstance(model, (torch.nn.DataParallel,
                              torch.nn.parallel.DistributedDataParallel)):
            logging.info("transfer model from data parallel to local.")
            model = model.module.to(device)

        zero_params = [torch.zeros_like(p.data) for p in model.parameters()
                       if p.requires_grad]
        trained_params = [torch.zeros_like(p.data) for p in model.parameters()
                          if p.requires_grad]
        for param, model_param in zip(trained_params, model.parameters()):
            param.data = model_param.data.clone()

        load_weights(model)
        init_server_params = model.parameters()
        update_local_variates(trained_params, zero_params, init_server_params,
                              self.server_controls, self.local_controls,
                              self.sample_num, self.batch_size, self.lr)
