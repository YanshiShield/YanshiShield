#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=missing-function-docstring, unused-argument
"""Extender UnitTest."""
import unittest

from neursafe_fl.python.coordinator.extenders import (broadcast_extender,
                                                      aggregate_extender,
                                                      finish_extender)


class TestExtenders(unittest.TestCase):
    """Test class."""

    def test_should_return_result_when_broadcast_extender_execute_success(self):
        test_params = {"job_name": "test"}

        def success_func(params):
            self.assertEqual(params, test_params)
            return {"file": None}, {"data": 0}
        result = broadcast_extender(success_func, test_params)
        self.assertEqual(result["files"], {"file": None})
        self.assertEqual(result["params"], {"data": 0})

    def test_should_raise_exception_when_broadcast_extender_execute_failed(self):
        test_params = {"job_name": "test"}

        def failed_func(params):
            self.assertEqual(params, test_params)
            raise ValueError

        with self.assertRaises(Exception):
            broadcast_extender(failed_func, test_params)

    def test_should_return_result_when_aggregate_extender_execute_success(self):
        previous_data = None

        def success_func(data, previous):
            self.assertEqual(data, 0)
            self.assertIsNone(previous)
            return [1]

        result = aggregate_extender(success_func, 0, previous_data)
        self.assertEqual(result, [1])

        def accumulate_func(data, previous):
            return previous + data

        result = aggregate_extender(accumulate_func, 10, previous=10)
        self.assertEqual(result, 20)

    def test_should_return_none_when_aggregate_extender_execute_failed(self):
        pass

    def test_should_return_result_when_finish_extender_execute_success(self):
        test_params = [1, 2, 3]

        def finish_func(params, aggregated_weights):
            res = sum(params)
            self.assertEqual(res, 6)

        finish_extender(finish_func, test_params, None)

    def test_should_return_empty_when_finish_extender_execute_failed(self):
        test_params = [1, 2, 3]

        def finish_func(params, aggregated_weights):
            raise NotImplementedError

        with self.assertRaises(Exception):
            finish_extender(finish_func, test_params, None)


if __name__ == "__main__":
    unittest.main()
