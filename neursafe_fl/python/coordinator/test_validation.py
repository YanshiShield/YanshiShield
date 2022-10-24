#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=missing-function-docstring
"""
UnitTest of validation
"""
import unittest
from neursafe_fl.python.coordinator.validations import (validate_config,
                                                        DEFAULT_HYPER_CONFIG)


class TestValidation(unittest.TestCase):
    """unittest class of validation
    """

    def setUp(self) -> None:
        self.test_config = None

    def test_should_validate_basic_params_of_federate_job_success(self):
        test_config = job_config()
        new_config = validate_config(test_config)
        self.assertIsNotNone(new_config)

    def test_should_raise_exception_when_basic_params_not_correct(self):
        test_config = job_config()
        test_config["job_name"] = "&*$dsd"  # wrong name
        with self.assertRaises(ValueError):
            validate_config(test_config)

        test_config = job_config()
        test_config["host"] = "ds.2d.3f"
        with self.assertRaises(ValueError):
            validate_config(test_config)

        test_config = job_config()
        test_config["model_path"] = 123
        with self.assertRaises(TypeError):
            validate_config(test_config)

    def test_should_raise_exception_when_lack_required_params(self):
        test_config = job_config()
        del test_config["job_name"]
        with self.assertRaises(ValueError):
            validate_config(test_config)

        test_config = job_config()
        del test_config["port"]
        with self.assertRaises(ValueError):
            validate_config(test_config)

    def test_should_raise_exception_when_hyper_params_not_correct(self):
        test_config = job_config()
        error_hyper = {"max_round_num": "string",
                       "threshold_client_num": 1.9}
        test_config["hyper_parameters"] = error_hyper
        with self.assertRaises(TypeError):
            validate_config(test_config)

    def test_should_set_default_hyper_config_when_not_fill_in(self):
        test_config = job_config()
        test_config["hyper_parameters"] = {}
        valid_config = validate_config(test_config)
        self.assertDictEqual(valid_config["hyper_parameters"],
                             DEFAULT_HYPER_CONFIG)

    def test_validate_secure_algorithm_when_parameters_all_correct(self):
        config = job_config()
        config["secure_algorithm"] = {
            "type": "Dp",
            "l2_norm_clip": 1.0,
            "noise_multiplier": 1.1,
            "adding_same_noise": False}

        validate_config(config)

    def test_validate_secure_algorithm_if_type_not_correct(self):
        config = job_config()
        config["secure_algorithm"] = {
            "type": 1,
            "l2_norm_clip": 1.0,
            "noise_multiplier": 1.1,
            "adding_same_noise": False}

        with self.assertRaises(TypeError):
            validate_config(config)

        try:
            validate_config(config)
        except TypeError as err:
            self.assertEqual(str(err), "Expect 'type' type: <class 'str'>, "
                                       "but got: <class 'int'>")

    def test_validate_secure_algorithm_if_type_not_supported(self):
        config = job_config()
        config["secure_algorithm"] = {
            "type": "mpc",
            "l2_norm_clip": 1.0,
            "noise_multiplier": 1.1,
            "adding_same_noise": False}

        try:
            validate_config(config)
        except ValueError as err:
            self.assertEqual(str(err),
                             "Secure algorithm: mpc is not supported"
                             ", support algorithm is ['DP', 'SSA']")

    def test_validate_secure_algorithm_if_noise_multiplier_not_correct(self):
        config = job_config()
        config["secure_algorithm"] = {
            "type": "DP",
            "l2_norm_clip": 1.0,
            "noise_multiplier": 1,
            "adding_same_noise": False}

        with self.assertRaises(TypeError):
            validate_config(config)

        try:
            validate_config(config)
        except TypeError as err:
            self.assertEqual(str(err), "Expect 'noise_multiplier' type: <class"
                                       " 'float'>, but got: <class 'int'>")

    def test_validate_secure_algorithm_if_adding_same_noise_not_correct(self):
        config = job_config()
        config["secure_algorithm"] = {
            "type": "DP",
            "l2_norm_clip": 1.0,
            "noise_multiplier": 1.1,
            "adding_same_noise": "False"}

        with self.assertRaises(TypeError):
            validate_config(config)

        try:
            validate_config(config)
        except TypeError as err:
            self.assertEqual(str(err),
                             "Expect 'adding_same_noise' type: "
                             "<class 'bool'>, but got: <class 'str'>")

    def test_validate_secure_algorithm_if_type_not_given(self):
        config = job_config()
        config["secure_algorithm"] = {
            "l2_norm_clip": 1.0,
            "noise_multiplier": 1.1,
            "adding_same_noise": False}

        with self.assertRaises(ValueError):
            validate_config(config)

    def test_validate_secure_algorithm_if_noise_multiplier_not_given(self):
        config = job_config()
        config["secure_algorithm"] = {
            "type": 'DP',
            "l2_norm_clip": 1.0,
            "adding_same_noise": False}

        with self.assertRaises(ValueError):
            validate_config(config)

    def test_validate_secure_algorithm_if_threshold_not_coorect(self):
        config = job_config()

        config["secure_algorithm"] = {
            "type": 'SSA',
            "threshold": 3}

        with self.assertRaises(ValueError):
            validate_config(config)

        config["secure_algorithm"] = {
            "type": 'SSA'}
        with self.assertRaises(ValueError):
            validate_config(config)

        config["hyper_parameters"]["client_num"] = 10
        config["hyper_parameters"]["threshold_client_num"] = 4
        with self.assertRaises(ValueError):
            validate_config(config)

    def test_should_validate_task_entry_be_success(self):
        config = job_config()
        del config["task_entry"]
        config["scripts"] = {
            "path": "{PROJECT_PATH}/fl/st/training/cfg/scripts/pytorch_mnist",
            "config_file": "pytorch_mnist.json"
        }
        validate_config(config)

    def test_should_raise_exception_when_task_entry_not_correct(self):
        config = job_config()
        del config["task_entry"]
        config["scripts"] = {
            "path": "{PROJECT_PATH}/fl/st/training/cfg/scripts/pytorch_mnist",
        }
        with self.assertRaises(ValueError):
            validate_config(config)

    def test_should_raise_exception_if_quantization_not_correct(self):
        config = job_config()

        # Compression type not correct
        config["compression"] = {"type": "error"}

        with self.assertRaises(ValueError):
            validate_config(config)

        # Quantization bits not exist
        config["compression"] = {"type": "quantization"}

        with self.assertRaises(ValueError):
            validate_config(config)

    CASE_NAME = (
        'TestValidation.'
        'test_validate_secure_algorithm_if_noise_multiplier_not_given')


def job_config():
    return {
        "job_name": "test",
        "description": "test case",
        "host": "0.0.0.0",
        "port": 9090,
        "clients": "0.0.0.1:34567",
        "model_path": "/tmp/init_model.h5",
        "runtime": "tensorflow",
        "task_entry": "{task_entry}",
        "hyper_parameters": {
            "max_round_num": 2,
            "client_num": 1,
            "threshold_client_num": 1,
            "evaluate_interval": 0,
            "save_interval": 0
        }
    }


if __name__ == "__main__":
    # import sys;sys.argv = ['', TestValidation.CASE_NAME]
    unittest.main()
