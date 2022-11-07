#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Generate init model for federated training.
"""
import tensorflow as tf


def _save_init_model():
    model = tf.keras.applications.VGG16(weights=None,
                                        include_top=True,
                                        input_shape=(32, 32, 3),
                                        classes=10)

    model.save("tf_vgg16.h5")


if __name__ == "__main__":
    _save_init_model()
