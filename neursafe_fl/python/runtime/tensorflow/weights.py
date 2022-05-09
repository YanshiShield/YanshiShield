#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Used to compute tensorflow weights.
"""

import numpy as np
from neursafe_fl.python.runtime.weights import WeightsCalculator

ENOUGH_MIN_FLOAT = 0.000001


class TensorflowWeightsCalculator(WeightsCalculator):
    """Used to add and subtract for tensorflow weights.
    """
    def add(self, x_weights, y_weights):
        """Compute x_weights + y_weights.
        """
        result = []
        for index, value in enumerate(x_weights):
            result.append(np.add(
                value, y_weights[index]))
        return result

    def subtract(self, x_weights, y_weights):
        """Compute x_weights - y_weights.
        """
        result = []
        for index, value in enumerate(x_weights):
            result.append(np.subtract(
                value, y_weights[index]))
        return result

    def multiply(self, x_weights, y):  # pylint:disable=invalid-name
        """Compute x_weights * y.
        """
        result = []
        for value in x_weights:
            result.append(np.multiply(value, y))
        return result

    def true_divide(self, x_weights, y):
        """Compute x_weights / y.
        """
        result = []
        for value in x_weights:
            result.append(np.true_divide(value, y))
        return result

    def equal(self, x_weights, y_weights):
        """compare x_weights == y_weights.
        """
        for index, value in enumerate(x_weights):
            result = abs(value - y_weights[index]) < ENOUGH_MIN_FLOAT
            if not result.all():
                return False
        return True
