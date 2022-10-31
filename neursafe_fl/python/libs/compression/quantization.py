#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
# pylint:disable=unused-argument, arguments-differ

"""
Quantization compression algorithm class
"""
import numpy as np

from neursafe_fl.python.libs.compression.base import Compression
import neursafe_fl.python.runtime.operation as op

DEFAULT_TARGET_BITS = 31


def check_quantization_bits(quantization_bits):
    """Check quantization bits parameter valid.
    """
    if not isinstance(quantization_bits, int):
        raise ValueError("The quantization_bits must be integer, provided "
                         "quantization_bits is: %s" % quantization_bits)

    if not 2 <= quantization_bits <= 16:
        raise ValueError("The quantization_bits must be in range [2, 16]. "
                         "Provided quantization_bits: %s" % quantization_bits)


class QuantizationCompression(Compression):
    """
    Quantization compression algorithm class definition.
    """

    def __init__(self, quantization_bits, **kwargs):
        """
        Args:
            quantization_bits: A integer specifying the quantization bitwidth
            target_bits: Compress integer numpy array by bit form into a integer
                value, the integer value bit width.
        """
        check_quantization_bits(int(quantization_bits))

        self.quantization_bits = int(quantization_bits)
        self.target_bits = DEFAULT_TARGET_BITS

    def pack_into_int(self, value: np.ndarray):
        """Pack integers in range [0, 2**`self.quantization_bits`-1] into
        integer values, concatenates the relevant bits of the input values into
        a sequence of integer values.

        example:
            value: [0, 1, 2, 3]
            self.quantization_bits: 2

            [00, 10, 01, 11] -> [[11100100]] -> [[228]]

        Args:
            value: integer numpy array
        """
        value = np.reshape(value, [-1, 1])
        value = self._expand_to_binary_form(value, self.quantization_bits)

        return self._pack_binary_form(value, self.target_bits).astype(np.int32)

    def unpack_into_int(self, value, shape: np.shape):
        """Unpack integers into the range of [0, 2**`self.quantization_bits`-1],
        to be used as the inverse of `pack_into_int` function.
        """
        value = self._expand_to_binary_form(value, self.target_bits)
        value = value[:np.product(shape) * self.quantization_bits]

        return np.reshape(self._pack_binary_form(
            value, self.quantization_bits), shape)

    def _expand_to_binary_form(self, value: np.ndarray, bits: np.ndarray):
        expand_array = np.array(
            [2 ** i for i in range(bits)], dtype=np.int32)

        bits_array = op.mod(op.floor_div(value, expand_array), 2)

        return np.reshape(bits_array, [-1])

    def _pack_binary_form(self, value: np.ndarray, bits: int):
        packing_array = np.array([[2 ** i] for i in range(bits)],
                                 dtype=np.int32)

        extra_zeros = np.zeros(np.mod(-value.size, bits),
                               dtype=np.int32)

        concatenated = op.concatenate(value, extra_zeros)

        reshaped = np.reshape(concatenated, [-1, bits])

        return np.matmul(reshaped, packing_array)

    def quantify(self, value: np.ndarray):
        """Quantify float numpy array into numpy integer array which value in
        range of [0, 2**`self.quantization_bits`-1], this operation corresponds
        to `t = round((t - min(t)) / (max(t) - min(t)) * (
        2**self.quantizaton_bits - 1))`.
        """
        min_ = np.min(value)
        max_ = np.max(value)

        if max_ == min_ and max_ == 0:
            return np.zeros_like(value, dtype=np.int32)

        if max_ == min_ and max_ != 0:
            return np.ones_like(value, dtype=np.int32)

        def probabilistic_quantization():  # pylint: disable=unused-variable
            """Probability quantification: assign the upper or lower bound value
            according to a certain probability
            """
            ceil_value = np.ceil(split_value)
            floor_value = np.floor(split_value)

            probability = np.random.uniform()
            flag = probability <= (ceil_value - split_value)

            return np.where(flag, floor_value, ceil_value).astype(np.int32)

        split_value = (value - min_) / (max_ - min_) * (
            2 ** self.quantization_bits - 1)

        # quantified_value = probabilistic_quantization()
        quantified_value = np.round(split_value).astype(np.int32)

        return quantified_value

    def unquantify(self, quantified_value: np.ndarray,
                   max_value: float, min_value: float):
        """the inverse of `quantify` function.
        """
        if max_value == min_value and max_value == 0:
            return np.zeros_like(quantified_value, dtype=np.float64)

        if max_value == min_value and max_value != 0:
            return np.ones_like(quantified_value, dtype=np.int32) * max_value

        return quantified_value * (max_value - min_value) / (
            2 ** self.quantization_bits - 1) + min_value

    def encode(self, value: np.ndarray):
        """Compress value.

        Args: numpy array
        """
        quantified_value = self.quantify(value)

        params = {"max_value": np.max(value),
                  "min_value": np.min(value),
                  "shape": value.shape}

        return self.pack_into_int(quantified_value), params

    def decode(self, quantified_value: np.ndarray,
               max_value: float, min_value: float, shape: np.shape):
        """Recover value from compressed value.

        Args:
            quantified_value: integer numpy array.
            max_value: the max value of raw numpy array(uncompressed array).
            min_value: the min value of raw numpy array(uncompressed array).
            shape: the shape of raw numpy array(uncompressed array).
        """
        quantified_value = self.unpack_into_int(quantified_value, shape)

        return self.unquantify(quantified_value, max_value, min_value)
