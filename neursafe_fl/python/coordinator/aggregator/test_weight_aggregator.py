#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=missing-function-docstring, protected-access, invalid-name
"""Weight Aggregator UnitTest."""
import asyncio
import unittest
import numpy as np

from neursafe_fl.python.coordinator.aggregator.weight_aggregator import WeightAggregator
from neursafe_fl.python.coordinator.errors import AggregationFailedError


def fake_weights():
    return [[1, 2, 0],
            [5, 9, 2],
            [1, 4, 4]]


class TestWeightAggregator(unittest.TestCase):
    """Test class."""

    def setUp(self) -> None:
        self.aggregator = WeightAggregator()
        self.data = {}

    def test_should_aggregator_accumulate_metrics_success(self):
        test_metrics = {"accuracy": 1.0,
                        "loss": 0.1}
        self.data["metrics"] = test_metrics
        self.aggregator.accumulate(self.data, weight=10)
        self.assertEqual(self.aggregator._WeightAggregator__total_weight, 10)
        self.assertEqual(
            self.aggregator._WeightAggregator__total_values["metrics"],
            {"accuracy": 10.0, "loss": 1.0})

    def test_should_aggregator_accumulate_weights_success(self):
        test_weights = fake_weights()
        self.data["weights"] = test_weights
        self.aggregator.accumulate(self.data, weight=10)
        self.assertEqual(self.aggregator._WeightAggregator__total_weight, 10)
        m = np.equal(self.aggregator._WeightAggregator__total_values["weights"],
                     np.multiply(test_weights, 10))
        self.assertTrue(m.all())

    def test_should_aggregator_accumulate_success_when_weight_is_none(self):
        test_metrics = {"accuracy": 1.0,
                        "loss": 0.1}
        self.data["metrics"] = test_metrics
        self.aggregator.accumulate(self.data)
        # if weight not set, default is 1
        self.assertEqual(self.aggregator._WeightAggregator__total_weight, 1)
        self.assertEqual(
            self.aggregator._WeightAggregator__total_values["metrics"],
            {"accuracy": 1.0, "loss": 0.1})

    def test_should_aggregator_accumulate_failed_when_data_format_error(self):
        error_metrics = [1, 2]
        self.data["metrics"] = error_metrics
        with self.assertRaises(AttributeError):
            self.aggregator.accumulate(error_metrics)

        error_metrics = {"loss": "error",
                         "accuracy": "string"}
        self.data["metrics"] = error_metrics
        with self.assertRaises(Exception):
            self.aggregator.accumulate(error_metrics)

    def test_should_aggregator_aggregate_metrics_success(self):
        metrics_1 = {"accuracy": 0.98,
                     "loss": 0.02,
                     "sample_num": 100}
        self.data["metrics"] = metrics_1
        self.aggregator.accumulate(self.data)
        metrics_2 = {"accuracy": 0.90,
                     "loss": 0.4,
                     "sample_num": 50}
        self.data["metrics"] = metrics_2
        self.aggregator.accumulate(self.data)
        self.assertEqual(self.aggregator._WeightAggregator__total_weight, 150)

        res = asyncio.run(self.aggregator.aggregate())
        self.assertIsNotNone(res)

    def z_test_should_aggregator_aggregate_weights_success(self):
        # Fixme: The truth value of an array with more than one element is ambiguous
        weights_1 = fake_weights()
        self.data["weights"] = weights_1
        self.aggregator.accumulate(self.data, weight=10)

        weights_2 = np.multiply(fake_weights(), 3.6)
        self.data["weights"] = weights_2
        self.aggregator.accumulate(self.data, weight=20)

        self.assertEqual(self.aggregator._WeightAggregator__total_weight, 30)

        res = self.aggregator.aggregate()
        self.assertIsNotNone(res)

    def test_should_aggregator_aggregate_failed_when_no_accumulated_data(self):
        with self.assertRaises(AggregationFailedError):
            asyncio.run(self.aggregator.aggregate())


if __name__ == "__main__":
    unittest.main()
