#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
Pull tensorflow MNIST data
"""

import os
import tensorflow as tf
from absl import app
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_string('path', None, 'Path for storing dataset.')


def main(argv):
    del argv

    data_path = FLAGS.path
    if not os.path.exists(data_path):
        os.makedirs(data_path)

    mnist = tf.keras.datasets.mnist
    mnist.load_data(
        os.path.join(data_path, "mnist.npz"))


if __name__ == '__main__':
    app.run(main)