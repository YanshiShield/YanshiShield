#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-few-public-methods
"""
Used differential privacy to protect pytorch weights.
"""
import collections
import torch

from neursafe_fl.python.runtime.security_algorithm import SecurityAlgorithm
from neursafe_fl.python.libs.secure.differential_privacy.dp_delta_weights \
    import DeltaWeightsDP


class PytorchDP(SecurityAlgorithm):
    """Define differential privacy method to protect pytroch weights.
    """
    def __init__(self, **kwargs):
        super().__init__()
        self.__secure_algorithm = kwargs["secure_algorithm"]
        self.__delta_weights_dp = DeltaWeightsDP(
            noise_multiplier=self.__secure_algorithm["noise_multiplier"])

    async def protect_weights(self, weights, **_):
        """Protect weights by differential privacy.

        Args:
            weights: need to be protected data.

        Returns:
            noised weights: weights which added noise by dp
        """
        noised_weights = collections.OrderedDict()
        for name, weight in weights.items():
            noised_weight = \
                self.__delta_weights_dp.add_noise_to_one_layer(
                    weight.numpy(),  # pylint:disable=no-member
                    self.__secure_algorithm.get("adding_same_noise", False))

            noised_weights[name] = torch.Tensor(
                noised_weight).to("cpu")

        return noised_weights
