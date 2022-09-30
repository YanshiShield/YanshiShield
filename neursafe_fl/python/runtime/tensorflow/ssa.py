#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-few-public-methods
"""Used secret share aggregate to protect tensorflow weights.
"""
import numpy as np

from neursafe_fl.python.runtime.security_algorithm import SecurityAlgorithm


class TensorflowSSA(SecurityAlgorithm):
    """Secret share aggregate method to protect tensorflow weights.
    """
    def __init__(self, **kwargs):
        super().__init__()
        self.__ssa_protector = kwargs['ssa_protector']

    async def protect_weights(self, weights, **kwargs):
        """Protect weights by secret share aggregate.

        Args:
            weights: need to be protected data.
            sample_num: the weight of weights.

        Returns:
            masked weights: weights which added mask by ssa.
        """
        sample_num = kwargs.get('sample_num', 1)
        await self.__ssa_protector.wait_ready()
        new_weights = []
        for weight in weights:
            new_weights.append(np.multiply(weight, sample_num))

        return self.__ssa_protector.encrypt(new_weights)
