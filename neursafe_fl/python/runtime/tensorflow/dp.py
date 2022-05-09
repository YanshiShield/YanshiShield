#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-few-public-methods
"""Used differential privacy to protect tensorflow weights.
"""
from neursafe_fl.python.runtime.security_algorithm import SecurityAlgorithm
from neursafe_fl.python.libs.secure.differential_privacy.dp_delta_weights \
    import DeltaWeightsDP


class TensorflowDP(SecurityAlgorithm):
    """Define differential privacy method to protect tensorflow weights.
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
            noised weights: weights which added noise by dp.
        """
        return self.__delta_weights_dp.add_noise_to_all_layers(
            list(weights),
            self.__secure_algorithm.get("adding_same_noise", False))
