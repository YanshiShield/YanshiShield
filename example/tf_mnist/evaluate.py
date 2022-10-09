#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Mnist evaluate for tensorflow.
"""

import argparse
import json
import logging
import os

import tensorflow as tf
import neursafe_fl as nsfl


_LOG = logging.getLogger(__name__)


def write_metrics(task_workspace, context):
    """Wirite metrics result
    """
    metrics_file = os.path.join(task_workspace, 'metrics.json')
    with open(metrics_file, 'w') as cfg_file:
        cfg_file.write(json.dumps(context))


def evaluate(index_range):
    """Do evaluate
    """
    mnist = tf.keras.datasets.mnist

    # Get dataset path in local
    data_path = nsfl.get_dataset_path("tf_mnist")
    (_, _), (x_test, y_test) = mnist.load_data(data_path)

    if index_range:
        range = index_range.split(",")
        x_test = x_test[int(range[0]):int(range[1])]
        y_test = y_test[int(range[0]):int(range[1])]

    print("data index range", index_range)
    print("test data length", len(x_test))

    x_test = x_test / 255.0

    model = tf.keras.models.Sequential([
        tf.keras.layers.Flatten(input_shape=(28, 28)),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(10, activation='softmax')
    ])

    model.compile(optimizer='sgd',
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])

    # load weights from server.
    nsfl.load_weights(model)

    fl_score = model.evaluate(x_test, y_test)
    metrics = {
        'loss': fl_score[0],
        'accuracy': fl_score[1]
    }
    # Comimit metrics. Then client agent will send it to server.
    nsfl.commit(metrics)


def main():
    """main
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--index_range', required=False,
                        help='Train data index range')
    args = parser.parse_args()
    evaluate(args.index_range)


if __name__ == '__main__':
    main()