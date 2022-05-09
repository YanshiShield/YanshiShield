#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Weight mean aggregator."""

from collections import OrderedDict

import numpy as np

from neursafe_fl.python.coordinator.aggregator.aggregator import Aggregator
from neursafe_fl.python.coordinator.errors import AggregationFailedError


class WeightAggregator(Aggregator):
    """Weight Aggregator calculate the weighted average(mean).

    Explanation:
        c = val1 * weight1 + val2 * weight2 / (weight1 + weight2)
    """
    def __init__(self, ssa_server=None):
        self.__total_values = {}
        self.__total_weight = 0
        self.__count = 0
        self.__ssa_server = ssa_server

    def accumulate(self, data, weight=None):
        """Accumulate the metrics and weights.

        The weight default is the sample number of training data, which is
        amount of data used by the client to train the model locally.

        Args:
            data: contains aggregated data, namely, 'weights' or 'metrics'
            weight: the weight value of this data
        """
        metrics = data.get("metrics")  # proto format
        if not weight:
            try:
                weight = metrics["sample_num"]
            except (ValueError, KeyError):
                weight = 1

        if metrics:
            self.__add_metrics(metrics, weight)

        if "weights" in data.keys():
            if self.__ssa_server:
                self.__total_values["weights"] = \
                    self.__ssa_server.ciphertext_accumulate(
                        data["weights"], data["client_id"])
            else:
                model_weights = data.get("weights")  # dict or list format
                self.__add_weights(model_weights, weight)

        self.__total_weight += weight

    def __add_metrics(self, metrics, weight):
        metrics_list = ["accuracy", "loss"]
        accumulated = self.__total_values.get("metrics", {})
        metrics_keys = list(metrics.keys())

        for key in metrics_list:
            if key not in metrics_keys:  # client not upload
                continue
            accumulated[key] = np.add(accumulated.get(key, 0),
                                      np.multiply(metrics[key], weight))

        self.__total_values["metrics"] = accumulated

    def __add_weights(self, model_weights, weight):
        accumulated = self.__total_values.get("weights", 0)
        if isinstance(model_weights, list):
            accumulated = np.add(accumulated,
                                 np.multiply(model_weights, weight))
        else:
            if not accumulated:
                accumulated = OrderedDict()
            for name, delta_w in model_weights.items():
                accumulated[name] = np.add(accumulated.get(name, 0),
                                           np.multiply(delta_w, weight))

        self.__total_values["weights"] = accumulated

    async def aggregate(self):
        """Calculate the weight average of the accumulated values."""
        if not self.__total_weight:
            raise AggregationFailedError("Weight Invalid.")
        weight_mean = {}
        if "metrics" in self.__total_values.keys():
            weight_mean["metrics"] = self.__aggregate_metrics()
        if "weights" in self.__total_values.keys():
            if self.__ssa_server:
                self.__total_values["weights"] = \
                    await self.__ssa_server.decrypt()
            weight_mean["weights"] = self.__aggregate_weights()

        return weight_mean

    def __aggregate_metrics(self):
        accumulated_metrics = self.__total_values["metrics"]
        mean = {}
        for key, value in accumulated_metrics.items():
            mean[key] = np.true_divide(value, self.__total_weight)
        return mean

    def __aggregate_weights(self):
        accumulated_weights = self.__total_values["weights"]
        if isinstance(accumulated_weights, dict):
            mean = OrderedDict()
            for name, delta_w in accumulated_weights.items():
                mean[name] = np.true_divide(delta_w, self.__total_weight)
            return mean

        mean = np.true_divide(accumulated_weights, self.__total_weight)
        return list(mean)
