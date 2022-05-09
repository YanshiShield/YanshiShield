#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=invalid-name, too-many-arguments, no-member,
# pylint:disable=no-name-in-module

"""FedProx Optimizer algorithm.
"""

import torch
from torch.optim.optimizer import Optimizer


class PerturbedGradientDescent(Optimizer):
    """Implements FedProx.
    """

    def __init__(self, origin_trainable_weights, learning_rate=0.01,
                 momentum=0, dampening=0,
                 weight_decay=0, nesterov=False, mu=0):

        if momentum < 0.0:
            raise ValueError("Wrong momentum: %s" % momentum)

        if learning_rate < 0.0:
            raise ValueError("Wrong learning rate: %s" % learning_rate)

        if weight_decay < 0.0:
            raise ValueError(
                "Wrong weight_decay: %s" % weight_decay)

        if nesterov and (momentum <= 0 or dampening != 0):
            raise ValueError(
                "If nesterov is true, momentum should be >= 0 or dampening "
                "not zero.")

        default_params = dict(learning_rate=learning_rate, momentum=momentum,
                              weight_decay=weight_decay, mu=mu,
                              dampening=dampening, nesterov=nesterov)
        super().__init__(origin_trainable_weights, default_params)

    def __setstate__(self, state):
        super().__setstate__(state)
        for param_group in self.param_groups:
            param_group.setdefault("nesterov", False)

    def step(self, closure=None):
        """Performs a single optimization step.

        Arguments:
            closure: reevaluates the model and returns the loss.
        """
        loss = closure() if closure else None

        for param_group in self.param_groups:
            weight_decay = param_group["weight_decay"]
            momentum = param_group["momentum"]
            dampening = param_group["dampening"]
            nesterov = param_group["nesterov"]
            mu = param_group["mu"]

            for param in param_group["params"]:
                if not param.grad:
                    continue

                delta_param = param.grad.data

                if weight_decay:
                    delta_param.add_(weight_decay, param.data)

                param_state = self.state[param]
                if "init" not in self.state[param]:
                    param_state["init"] = torch.clone(param.data).detach()

                if momentum:
                    if "momentum_buffer" not in param_state:
                        param_state["momentum_buffer"] = torch.clone(
                            delta_param).detach()
                        buffer = param_state["momentum_buffer"]
                    else:
                        buffer = param_state["momentum_buffer"]
                        buffer.mul_(momentum).add_(1 - dampening, delta_param)

                    if nesterov:
                        delta_param = delta_param.add(momentum, buffer)
                    else:
                        delta_param = buffer

                delta_param.add_(mu, param.data - param_state["init"])
                param.data.add_(-param_group["learning_rate"], delta_param)

        return loss
