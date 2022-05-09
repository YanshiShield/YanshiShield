#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
Differential Privacy will protect private information of data.
"""

import math
import collections
import numpy as np
from absl import logging

from neursafe_fl.python.libs.secure.differential_privacy.errors import \
    DPGeneratorError

LogMoment = collections.namedtuple("LogMoment", ["moment_order",
                                                 "log_moment"])


class DPGenerator:
    """Differentially private class

    The class DPGenerator use to add Gaussian noise to data which needed
    protection. It has two methods 'compute_privacy_spent', 'add_noise'
    The first method will calculate the privacy budget spent, and the
    second will add noise to data.

    We further assume that let u_0 denote the probability density function
    of N(0, sigma^2), and u_1 denote the probability density function of
    N(1, sigma^2), then wo need to compute the log of the moment generating
    function evaluated at the value i is that:
        logMGF(i) = log(max(E_1, E_2))
    where:
        E_1 = E[(u_0(z)/u_1(z))^i], z~u_0
        E_2 = E[(u_1(z)/u_0(z))^i], z~u_1
    """

    def __init__(self, noise_stddev, max_moment_order=32, delta=1e-5):
        """Initialize the DPGeneratorClass.

        Args:
          noise_stddev: the standard deviation of the Gaussian noise
          max_moment_order: the max value of moment order
          delta: the correction item which we compute the corresponding
            epsilon, which is the parameter of (epsilon, delta) dp algorithm
        """
        self.__deviation = noise_stddev
        self.__delta = delta
        self.__max_moment_order = max_moment_order

    def __compute_log_moment(self, deviation, moment_order):
        """Compute high moment of privacy loss.

        we can compute E_1 and E_2, let moment_order equals to i, then
        E_1 = E_2 = exp(i*(i+1)/(2*deviation^2)), so we can calculate
        log moment equals to i*(i+1)/(2*deviation^2)
        Args:
          deviation: standard deviation of gaussian distribution.
          moment_order: the order of moment.
        Returns:
          log(max(E_1, E_2))
        """
        return moment_order * (moment_order + 1) / (2 * deviation**2)

    def __compute_eps(self, log_moments, delta):
        """According to Tail bound, we can compute epsilon

        Tail bound:delta = min exp(log_moment(i) - i * epsilon)

        Args:
          log_moments: th LogMoment array
          delta: the parameter of (epsilon, delta) dp algorithm
        """
        min_eps = float("inf")
        for moment_order, log_moment in log_moments:
            min_eps = min(min_eps, (log_moment - math.log(
                delta)) / moment_order)

        logging.info("the min epsilon is %s", min_eps)
        return min_eps

    def compute_privacy_spent(self, step):
        """Compute privacy spent after adding noise steps times.

        Suppose tha a mechanism M consists of a sequence of adaptive mechanism
        M_1, M_2,...,M_k, then the log moment of mechanism M equals to sum of
        the log moment of mechanism M_1, M_2,...,M_k

        If every step, we use same mechanism, then the log moment of mechanism
        M is k * the log moment of mechanism M_i

        Args:
          step: already add noise step number times
        """
        if step < 1:
            raise DPGeneratorError("step value: %s is meaningless if "
                                   "less than 1." % step)

        log_moments = []
        for moment_order in range(1, self.__max_moment_order + 1):
            log_moment = step * self.__compute_log_moment(self.__deviation,
                                                          moment_order)
            log_moments.append(LogMoment(moment_order, log_moment))

        return self.__compute_eps(log_moments, self.__delta)

    def add_noise(self, data, adding_same_noise=True):
        """Add Gaussian noise to protection data

        Args:
          data: data which needed to add noise for protection, the data must
            be numpy array.
          adding_same_noise: whether add same noise to every element of
            data to be protected.

        Returns:
          noised data: data which has already be added Gaussian noise.

        Raises:
          DPGeneratorError: An error occurred when adding noise.
        """
        if not isinstance(data, np.ndarray):
            raise DPGeneratorError("Parm: Data to be protected is not numpy "
                                   "array.")

        try:
            if adding_same_noise:
                noise = np.random.normal(0, self.__deviation)
            else:
                noise = np.random.normal(0, self.__deviation,
                                         data.shape)

            return np.add(data, noise)
        except Exception as err:
            logging.exception(str(err))
            raise DPGeneratorError("Internal error when adding noise.") from err
