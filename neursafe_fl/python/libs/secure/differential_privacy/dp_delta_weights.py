#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
Differential Privacy in federated learning will protect delta weights.
"""

import numpy as np

from neursafe_fl.python.libs.secure.differential_privacy.errors import \
    DPGeneratorError
from neursafe_fl.python.libs.secure.differential_privacy.dp_generator import \
    DPGenerator


class DeltaWeightsDP:
    """Delta weights with differential privacy.

    The class DeltaWeightsDP use to add Gaussian noise to delta trainable
    weights of model. It has three methods 'add_noise_to_all_layers',
    'add_noise_to_one_layer' and 'get_privacy_spent'. The first method will
    add noise to delta weights of all layers, while second will add noise to
    delta weights of assigned layer, the last method will return privacy
    budget spent.

    Delta weights is model updating information in federated learning process,
    which will sent from client to coordinator. It will be calculated by model
    weights after training subtract model weights before training.
    """

    def __init__(self, noise_multiplier):
        """Initialize the DeltaWeightsDP class.

        Args:
            noise_multiplier: the standard deviation of Gaussian noise.
        """
        self.__noise_multiplier = noise_multiplier
        self.__dp_generator = DPGenerator(
            noise_stddev=noise_multiplier)

    def add_noise_to_all_layers(self, delta_weights_list,
                                adding_same_noise=True):
        """Add noise to delta weights of all trainable layers.

        Args:
            delta_weights_list: delta weights of all layers, which is a list
            of numpy array. adding_same_noise: whether add same noise to every
            weight of some layer weights.
            adding_same_noise: whether add same noise to every weight of layer
            weights.

        Returns:
            noised delta weights list, delta weights list which has already be
            added Gaussian noise.

        Raises:
            DPGeneratorError: An error occurred when adding noise.
        """
        if not isinstance(delta_weights_list, list):
            raise DPGeneratorError("parm delta weights list: %s is not list"
                                   % delta_weights_list)

        noised_delta_weights_list = []
        for delta_weights in delta_weights_list:
            noised_delta_weights_list.append(
                self.add_noise_to_one_layer(delta_weights, adding_same_noise))

        return noised_delta_weights_list

    def add_noise_to_one_layer(self, delta_weights, adding_same_noise=True):
        """Add noise to delta weights of some trainable layer.

        Args:
            delta_weights: delta weights of some layer, which is numpy array.
            adding_same_noise: whether add same noise to every weight of layer
            weights.

        Returns:
            noised delta weights, delta weights which has already be added
            Gaussian noise.

        Raises:
            DPGeneratorError: An error occurred when adding noise.
        """
        if not isinstance(delta_weights, np.ndarray):
            raise DPGeneratorError("parm delta weights: %s is not numpy array"
                                   % delta_weights)

        return self.__dp_generator.add_noise(
            delta_weights,
            adding_same_noise=adding_same_noise)

    def get_privacy_spent(self, steps):
        """Compute privacy spent based on moment accounts

        Compute the privacy budget spent iterated over steps num with adding
        noise to delta weights.

        Args:
            steps: The number of steps which means the times of adding noise.

        Returns:
            privacy_spent

        Raises:
            DPGeneratorError: An error occurred when get privacy spent.
        """
        return self.__dp_generator.compute_privacy_spent(steps)
