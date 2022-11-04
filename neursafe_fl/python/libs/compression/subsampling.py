#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
# pylint:disable=unused-argument, arguments-differ

"""
Subsampling compression algorithm class
"""
import time

import numpy as np

from neursafe_fl.python.libs.compression.base import Compression


def check_sampling_rate(sampling_rate):
    """Check sampling rate valid.
    """
    if not isinstance(sampling_rate, float):
        raise ValueError("The sampling_rate must be float, provided "
                         "sampling_rate is: %s" % sampling_rate)

    if not 0 < sampling_rate < 1:
        raise ValueError("The sampling_rate must be in range (0, 1). "
                         "Provided sampling_rate: %s" % sampling_rate)


def gen_seed():
    """Generate random seed.
    """
    return int(time.time() % 10000)


class SubsamplingCompression(Compression):
    """Subsampling compression algorithm class definition.

    Compress data by sampling. It will extract subset of data, steps as follows:

    1. Generate a seed and generate a random 0,1 mask matrix, in which the
       proportion of 0 is the same as the set parameter sampling_rate, because 0
       means to be reserved, 1 means it will be masked.

        original data: [[1, 2], [3, 4]]
        mask matrix: [[0, 1], [1, 0]]
        masked data: [1, 3]

    2. According to the shape of original data and the same seed generated in
       step 1, then we reconstruct data.

       masked weight: [1, 3]
       mask matrix: [[0, 1], [1, 0]]
       reconstructed data: [[1, 0], [3, 0]]
    """

    def __init__(self, sampling_rate, **kwargs):
        """
        Args:
            sampling_rate: Specify the sampling ratio, how much data needs to be
                sampled from the original data, which can be simply understood
                as the compression ratio
        """
        check_sampling_rate(sampling_rate)

        self.sampling_rate = sampling_rate

    def encode(self, value: np.ndarray):
        """Compress value.

        Args:
            value: numpy array.
        """
        seed = gen_seed()
        np.random.seed(seed=seed)
        mask = np.random.choice([0, 1], value.shape,
                                p=[self.sampling_rate, 1 - self.sampling_rate])

        masked = np.ma.masked_array(value, mask=mask).compressed()

        params = {"shape": value.shape,
                  "seed": seed}

        return masked, params

    def decode(self, masked_value: np.ndarray, shape: np.shape, seed: int):
        """Reconstruct data from compressed data.

        Args:
            masked_value: masked value(subsampled value).
            shape: the shape of raw numpy array(uncompressed array).
            seed: the random seed, must be same with the seed in encoding.
        """
        np.random.seed(seed=seed)
        mask = np.random.choice(
            [np.inf, 0.0], shape,
            p=[self.sampling_rate, 1 - self.sampling_rate]).flatten()

        np.place(mask, mask == np.inf, masked_value)

        return np.reshape(mask, shape)
