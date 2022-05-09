#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Mnist train for tensorflow.
"""

import argparse
import logging
import neursafe_fl as nsfl
from tensorflow import keras as ks

import tensorflow as tf
_LOG = logging.getLogger(__name__)

learning_rate=0.15


def train(index_range):
    """Train.
    """
    mnist = tf.keras.datasets.mnist

    # Get dataset path in local
    data_path = nsfl.get_dataset_path("tf_mnist")
    (x_train, y_train), (_, _) = mnist.load_data(data_path)

    if index_range:
        range = index_range.split(",")
        x_train = x_train[int(range[0]):int(range[1])]
        y_train = y_train[int(range[0]):int(range[1])]

    x_train = x_train / 255.0

    print("data index range", index_range)
    print("train data length", len(x_train))

    model = tf.keras.models.Sequential([
        tf.keras.layers.Flatten(input_shape=(28, 28)),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(10, activation='softmax')
    ])

    optimizer = ks.optimizers.SGD(lr=learning_rate)
    model.compile(optimizer=optimizer,
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])

    # Load weights from server.
    nsfl.load_weights(model)
    history = model.fit(x_train, y_train, epochs=1)
    print('loss', history.history['loss'])
    print('accuracy:', history.history['accuracy'])

    # save weights to task worksapce, the client agent will compute delta
    # weights and send it to server.
    nsfl.commit_weights(model)

    metrics = {
        'sample_num': len(x_train),
        'loss': history.history['loss'][-1],
        'accuracy': history.history['accuracy'][-1]
    }
    # write metrics to task worspace, and client agent will send it to server.
    nsfl.commit_metrics(metrics)


def main():
    """Train entry.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--index_range', required=False,
                        help='Train data index range')
    args = parser.parse_args()

    train(args.index_range)


if __name__ == '__main__':
    main()
