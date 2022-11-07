#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
Used to compute pytorch weights.
"""

from collections import OrderedDict
import numpy as np
import torch

from neursafe_fl.python.runtime.weights import (WeightsCalculator,
                                                WeightsConverter, WEIGHT)

ENOUGH_MIN_FLOAT = 0.000001


class PytorchWeightsCalculator(WeightsCalculator):
    """Used to add and subtract for pytorch weights.
    """
    def add(self, x_weights, y_weights):
        """Compute x_weights + y_weights.

        The result will be saved in x_weights, the x_weights will be changed.
        """
        for name, y_item in y_weights.items():
            # w1[name1] = w2[name1] + t1
            x_weights[name] = np.add(x_weights[name].cpu(), y_item.cpu())
        return x_weights

    def subtract(self, x_weights, y_weights):
        """Compute x_weights - y_weights.

        The result will be saved in x_weights, the x_weights will be changed.
        """
        for name, y_item in y_weights.items():
            # w1[name1] = w2[name1] + t1
            x_weights[name] = np.subtract(x_weights[name].cpu(), y_item.cpu())

        return x_weights

    def multiply(self, x_weights, y):  # pylint:disable=invalid-name
        """Compute x_weights * y.
        """
        result = OrderedDict()
        for name, delta_w in x_weights.items():
            result[name] = np.multiply(delta_w, y)
        return result

    def true_divide(self, x_weights, y):  # pylint:disable=invalid-name
        """Compute x_weights / y.
        """
        result = OrderedDict()
        for name, delta_w in x_weights.items():
            result[name] = np.true_divide(delta_w.cpu(), y.cpu())
        return result

    def equal(self, x_weights, y_weights):
        """compare x_weights == y_weights.
        """
        for name, y_item in y_weights.items():
            result = abs(x_weights[name] - y_item) < ENOUGH_MIN_FLOAT
            if not result.all():
                return False
        return True


class PytorchWeightsConverter(WeightsConverter):
    """Weights converter executing in pytorch runtime.
    """

    def encode(self, raw_weights, encoder):
        """Encode weights according to specified encoder.
        """
        internal_weights = []

        for name, weight in raw_weights.items():
            encoded_weight, params = encoder.encode(weight.numpy())
            internal_weight = WEIGHT(name, encoded_weight, params)
            internal_weights.append(internal_weight)

        return internal_weights

    def decode(self, internal_weights, decoder):
        """Decode weights according to specified decoder.
        """
        raw_weights = OrderedDict()

        for internal_weight in internal_weights:
            raw_weight = decoder.decode(internal_weight.weight,
                                        **internal_weight.params)
            raw_weights[internal_weight.id] = torch.from_numpy(raw_weight)

        return raw_weights
