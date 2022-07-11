#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
Pytorch model in FL.
"""

import torch
import torch.nn as nn

from neursafe_fl.python.runtime.model import Model, LoadWeightsError


class PytorchModel(Model):
    """Pytorch model, used to save and load weight for pytorch.
    """
    def __init__(self, **kwargs):
        self.__model = kwargs.get('model', None)

    def save(self, obj, path, **kwargs):
        """Save weights to local path.

        Args:
            obj: Weights or model to save the weights.
            path: The file where to save weights.
        """
        if isinstance(obj, nn.Module):
            if isinstance(obj, (torch.nn.DataParallel,
                                torch.nn.parallel.DistributedDataParallel)):
                torch.save(obj.module.to("cpu").state_dict(), path)
            else:
                torch.save(obj.state_dict(), path)
        else:
            torch.save(obj, path)

    def load(self, path, **kwargs):
        """Load model/weights from local file.

        Args:
            path: The file where to load weights.
            kwargs:
                return_type: Model or weights, default is weights.
        """
        weights = torch.load(path)

        if self.__model:
            self.__model.load_state_dict(weights)

        if kwargs.get('return_type', 'weights') == 'weights':
            return weights

        if not self.__model:
            raise LoadWeightsError(
                'Load weights failed, not have base model to load weights.')
        return self.__model
