#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Train VGG16 in cifar10 dataset
"""

import argparse

import tensorflow as tf

import neursafe_fl as nsfl


def train(index_range):
    """train model
    """
    cifar10 = tf.keras.datasets.cifar10
    nb_classes = 10

    (x_train, y_train), (_, _) = cifar10.load_data()

    if index_range:
        range = index_range.split(",")
        x_train = x_train[int(range[0]):int(range[1])]
        y_train = y_train[int(range[0]):int(range[1])]

    print("data index range", index_range)
    print("train data length", len(x_train))

    y_train = tf.keras.utils.to_categorical(y_train, nb_classes)

    model = tf.keras.applications.VGG16(weights=None,
                                        include_top=True,
                                        input_shape=x_train.shape[1:],
                                        classes=nb_classes)

    model.compile(
        optimizer=tf.keras.optimizers.SGD(lr=0.005, decay=1e-6, momentum=0.9,
                                          nesterov=True),
        loss="categorical_crossentropy", metrics=["accuracy"])

    nsfl.load_weights(model)

    history = model.fit(x_train, y_train, epochs=1, batch_size=256)
    print("loss", history.history["loss"])
    print("accuracy:", history.history["accuracy"])

    metrics = {
        "sample_num": len(x_train),
        "loss": history.history["loss"][-1],
        "accuracy": history.history["accuracy"][-1]
    }

    nsfl.commit(metrics, model)


def main():
    """Train entry.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--index_range", required=False,
                        help="Train data index range")
    args = parser.parse_args()

    train(args.index_range)


if __name__ == "__main__":
    main()