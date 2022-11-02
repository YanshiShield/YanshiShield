#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Evaluate VGG16 in cifar10 dataset
"""

import argparse

import tensorflow as tf
import neursafe_fl as nsfl


def evaluate(index_range):
    cifar10 = tf.keras.datasets.cifar10
    nb_classes = 10

    (_, _), (x_test, y_test) = cifar10.load_data()
    if index_range:
        range = index_range.split(",")
        x_test = x_test[int(range[0]):int(range[1])]
        y_test = y_test[int(range[0]):int(range[1])]

    print("data index range", index_range)
    print("test data length", len(x_test))

    y_test = tf.keras.utils.to_categorical(y_test, nb_classes)

    model = tf.keras.applications.VGG16(weights=None,
                                        include_top=True,
                                        input_shape=x_test.shape[1:],
                                        classes=nb_classes)

    model.compile(
        optimizer=tf.keras.optimizers.SGD(lr=0.005, decay=1e-6, momentum=0.9,
                                          nesterov=True),
        loss="categorical_crossentropy", metrics=["accuracy"])

    nsfl.load_weights(model)

    score = model.evaluate(x_test, y_test)
    metrics = {
        "sample_num": len(x_test),
        "loss": score[0],
        "accuracy": score[1]
    }

    print("Evaluate metrics: ", metrics)

    nsfl.commit(metrics)


def main():
    """main
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--index_range", required=False,
                        help="Train data index range")
    args = parser.parse_args()
    evaluate(args.index_range)


if __name__ == "__main__":
    main()
