#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Generate init model for federated training.
"""
import torch

from train import LeNetModel

def _save_init_weights():
    model = LeNetModel()

    torch.save(model.state_dict(), "torch_cifar10_feddc.pth")


if __name__ == "__main__":
    _save_init_weights()
