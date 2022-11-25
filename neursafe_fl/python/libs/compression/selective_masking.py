#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
# pylint:disable=unused-argument, arguments-differ

"""
Selective masking compression algorithm.
"""

import numpy as np

from neursafe_fl.python.libs.compression.base import Compression


def check_top_k_ratio(top_k_ratio):
    """Check top-k ratio valid.
    """
    if not isinstance(top_k_ratio, float):
        raise ValueError("The top_k_ratio must be float, provided "
                         "top_k_ratio is: %s" % top_k_ratio)

    if not 0 < top_k_ratio < 1:
        raise ValueError("The top_k_ratio must be in range (0, 1). "
                         "Provided top_k_ratio: %s" % top_k_ratio)


class SelectiveMasking(Compression):
    """Selective masking compression definition.

    This algorithm will select top K largest absolute difference value of data
    which need to be compressed. We will set sampling ratio(top_k_ratio), it
    means that the value k equals sampling ratio multiplied with the number of
    elements of the data.
    """
    def __init__(self, top_k_ratio, **kwargs):
        """
        Args:
            top_k_ratio: Specify the sampling ratio, how much top k data will be
                selected from the original data, which can be simply understood
                as the compression ratio.
        """
        check_top_k_ratio(top_k_ratio)
        self.top_k_ratio = top_k_ratio

    def encode(self, value: np.ndarray):
        """Compress value.

        Args:
            value: numpy array.

        Returns:
            masked_value: Selected top k values.
            params: A dict include the shape of raw array and the indexes of
                masked_value.
        """
        value_ = value.flatten()
        abs_value_ = np.abs(value_)
        top_k_length = int(self.top_k_ratio * value_.size)

        top_k_ind = np.argpartition(abs_value_, -top_k_length)[-top_k_length:]

        masked_value = value_[top_k_ind]

        params = {"shape": value.shape,
                  "ind": top_k_ind.astype(np.int32).tolist()}

        return masked_value, params

    def decode(self, masked_value: np.ndarray, ind: list, shape: np.shape):
        """Reconstruct data from compressed data.

        Args:
            masked_value: masked value(compressed value).
            ind: the indexes of masked value in raw array(uncompressed array).
            shape: the shape of raw numpy array(uncompressed array).
        """
        raw_value = np.zeros(np.prod(shape))

        np.put(raw_value, ind, masked_value)

        return np.reshape(raw_value, shape)
