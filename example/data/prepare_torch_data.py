#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
Pull Pytorch MNIST data
"""

import os
import torchvision
from absl import flags
from absl import app

FLAGS = flags.FLAGS

flags.DEFINE_string('path', None, 'Path for storing dataset.')


def main(argv):
    del argv

    data_path = FLAGS.path

    if not os.path.exists(data_path):
        os.makedirs(data_path)

    torchvision.datasets.MNIST(data_path, download=True)


if __name__ == '__main__':
    app.run(main)