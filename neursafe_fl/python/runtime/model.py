#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
Basic class for different runtime models.
"""

import abc


class LoadWeightsError(Exception):
    """load weights failed
    """


class Model:
    """Basic model class.

    Define general abstract method for different runtime.
    """

    @abc.abstractmethod
    def save(self, obj, path, **kwargs):
        """Save model/weights to local path.

        Args:
            obj: Model or weights
            path: The file where to save
            kwargs:
                save_type: Saved with model or weights, used in tensorflow
        """

    @abc.abstractmethod
    def load(self, path, **kwargs):
        """Load model/weights from local file

        Args:
            path: The file where to load model or weights
            kwargs:
                load_type: Model or weights, used in tensorflow.
                return_type: Model or weights.
                need_compile: Used in tensorflow.
        """

    @abc.abstractmethod
    def cache_init_weights(self, path):
        """Cache init weights from local file to memory

        Args:
            path: The file where to load model or weights
        """

    @abc.abstractmethod
    def set_raw_model(self, model):
        """Refresh raw model

        Args:
            model: new model
        """

    @property
    def weights(self):
        """
        Return current model weights.
        """

    @property
    def raw_model(self):
        """
        Return raw model
        """
