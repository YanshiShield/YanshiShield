#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Tensorflow model in FL.
"""

import tensorflow as tf

from neursafe_fl.python.runtime.model import Model, LoadWeightsError


class TensorflowModel(Model):
    """Tensorflow model, used to save and load weight/model for tensorflow.
    """
    def __init__(self, **kwargs):
        self.__model = kwargs.get('model', None)

    def save(self, obj, path, **kwargs):
        """Save model/weights to local path.

        Args:
            obj: Model or weights.
            path: The file where to save.
            kwargs:
                save_type: Saved with model or weights, used in tensorflow.
        """
        if isinstance(obj, tf.keras.Model):
            if kwargs.get('save_type', 'model') == 'model':
                obj.save(path)
                tf.keras.backend.clear_session()
            else:
                obj.save_weights(path)
        else:
            self.__model.set_weights(obj)
            if kwargs.get('save_type', 'model') == 'model':
                self.__model.save(path)
            else:
                self.__model.save_weights(path)

    def load(self, path, **kwargs):
        """Load model/weights from local file

        Args:
            path: The file where to load model or weights.
            kwargs:
                load_type: model or weights, default is model,
                    used in tensorflow.
                return_type: Model or weights, default is weights.
                need_compile: Used in tensorflow.
        """
        if kwargs.get('load_type', 'model') == 'model':
            self.__model = tf.keras.models.load_model(
                path, compile=kwargs.get('need_compile', False))
            # when not use tf.keras.backend.clear_session(), this will be
            # memory leak solution reference:
            # https://github.com/tensorflow/tensorflow/issues/35524
            tf.keras.backend.clear_session()
            if kwargs.get('return_type', 'weights') == 'weights':
                return self.__model.get_weights()
            return self.__model

        if self.__model is not None:
            self.__model.load_weights(path)
            if kwargs.get('return_type', 'weights') == 'weights':
                return self.__model.get_weights()
            return self.__model

        raise LoadWeightsError(
            'Load weights failed, not have base model to load weights.')
