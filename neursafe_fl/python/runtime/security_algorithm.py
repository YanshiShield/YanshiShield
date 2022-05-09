#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-few-public-methods
"""Basic class for differential privacy protect delta weights.
"""
import abc


class SecurityAlgorithm:
    """Basic security algorithm class.

    used some SecurityAlgorithm to protect delta weights.
    Args:
        secure_algorithm: the config of secure_algorithm
    """
    def __init__(self):
        self._security_algorithm = None
        # example:
        # self._security_algorithm = fl.secure.create_secure_algorithm_handler(
        #    kwargs['secure_algorithm'], kwargs['sample_num'])

    @abc.abstractmethod
    async def protect_weights(self, weights, **kwargs):
        """Protect weights by differential privacy

        Args:
            weights: need to be protected data.

        Returns:
            noised weights: weights which added noise by dp
        """
