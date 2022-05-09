#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
Basic class for different runtime to complete weights.
"""

import abc


class WeightsCalculator:
    """Basic weights Calculator, add and subtract weights.

    Define general abstract method for different runtime to complete weights.
    """
    @abc.abstractmethod
    def add(self, x_weights, y_weights):
        """Compute x_weights + y_weights.
        """

    @abc.abstractmethod
    def subtract(self, x_weights, y_weights):
        """Compute x_weights - y_weights.
        """

    @abc.abstractmethod
    def multiply(self, x_weights, y):  # pylint:disable=invalid-name
        """Compute x_weights * y.
        """

    @abc.abstractmethod
    def true_divide(self, x_weights, y):  # pylint:disable=invalid-name
        """Compute x_weights / y.
        """

    @abc.abstractmethod
    def equal(self, x_weights, y_weights):
        """compare x_weights == y_weights.
        """
