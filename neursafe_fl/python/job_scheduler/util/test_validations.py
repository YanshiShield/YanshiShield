#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint: disable=missing-function-docstring, missing-class-docstring
# pylint: disable=too-many-public-methods
"""
test validation function
"""
import unittest

from neursafe_fl.python.job_scheduler.util.validations import \
    validate_job_config, validate_heartbeat


class ValidationJobConfigTest(unittest.TestCase):

    def setUp(self) -> None:
        self.__job_config = {
            "id": 'fl-job',
            "description": "test",
            "runtime": "pytorch",
            "port": 8080,
            "clients": "1.2.3.4:8080",
            "model_path": "fl_mnist",
            "task_entry": "fl",
            "output": "aaaa"
        }

    def __check_err_msg(self, correct_err_msg):
        try:
            validate_job_config(self.__job_config)
        except (ValueError, TypeError) as error:
            self.assertEqual(str(error),
                             correct_err_msg)

    def test_check_job_config_successfully(self):
        validate_job_config(self.__job_config)

    def test_raise_exception_if_id_not_exist(self):
        del self.__job_config["id"]
        self.assertRaises(ValueError, validate_job_config, self.__job_config)

        err_msg = "Required key: 'id' not exist in job"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_id_not_str_type(self):
        self.__job_config["id"] = 1
        self.assertRaises(TypeError, validate_job_config, self.__job_config)

        err_msg = "Expect 'id' type: <class 'str'>, " \
                  "but got: <class 'int'> in job"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_id_not_match_re_rule(self):
        self.__job_config["id"] = "s_s"
        self.assertRaises(ValueError, validate_job_config, self.__job_config)

        err_msg = "s_s not satisfied with pattern: " \
                  "[a-z0-9]([-a-z0-9]{0,98}[a-z0-9])?$"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_description_not_str_type(self):
        self.__job_config["description"] = 1
        self.assertRaises(TypeError, validate_job_config, self.__job_config)

        err_msg = "Expect 'description' type: <class 'str'>, " \
                  "but got: <class 'int'> in job"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_model_id_not_str_type(self):
        self.__job_config["model_path"] = 1
        self.assertRaises(TypeError, validate_job_config, self.__job_config)

        err_msg = "Expect 'model_path' type: <class 'str'>, " \
                  "but got: <class 'int'> in job"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_runtime_not_exist(self):
        del self.__job_config["runtime"]
        self.assertRaises(ValueError, validate_job_config, self.__job_config)

        err_msg = "Required key: 'runtime' not exist in job"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_runtime_not_str_type(self):
        self.__job_config["runtime"] = 1
        self.assertRaises(TypeError, validate_job_config, self.__job_config)

        err_msg = "Expect 'runtime' type: <class 'str'>, " \
                  "but got: <class 'int'> in job"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_runtime_not_supported(self):
        self.__job_config["runtime"] = "sss"
        self.assertRaises(ValueError, validate_job_config, self.__job_config)

        err_msg = "Runtime: sss not in supported runtime: ['TENSORFLOW', 'PYTORCH']."
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_clients_not_str_type(self):
        self.__job_config["clients"] = 1
        self.assertRaises(TypeError, validate_job_config, self.__job_config)

        err_msg = "Expect 'clients' type: <class 'str'>, " \
                  "but got: <class 'int'> in job"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_port_not_int_type(self):
        self.__job_config["port"] = '8080'
        self.assertRaises(TypeError, validate_job_config, self.__job_config)

        err_msg = "Expect 'port' type: <class 'int'>, " \
                  "but got: <class 'str'> in job"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_port_not_in_correct_range(self):
        self.__job_config["port"] = 80
        self.assertRaises(ValueError, validate_job_config, self.__job_config)

        err_msg = "Port: 80 must in range 1024~65535."
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_task_entry_and_scripts_both_not_exist(self):
        del self.__job_config["task_entry"]
        self.assertRaises(ValueError, validate_job_config, self.__job_config)

        err_msg = "Mutex parameters: ['task_entry', 'scripts'] must exist one."
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_task_entry_not_str_type(self):
        self.__job_config["task_entry"] = 1
        self.assertRaises(TypeError, validate_job_config, self.__job_config)

        err_msg = "Expect 'task_entry' type: <class 'str'>, " \
                  "but got: <class 'int'> in job"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_scripts_not_dict_type(self):
        self.__job_config["scripts"] = 'sss'
        self.assertRaises(TypeError, validate_job_config, self.__job_config)

        err_msg = "Expect 'scripts' type: <class 'dict'>, " \
                  "but got: <class 'str'> in job"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_path_of_scripts_not_exist(self):
        self.__job_config["scripts"] = {"config_file": "ssss"}
        self.assertRaises(ValueError, validate_job_config, self.__job_config)

        err_msg = "Required key: 'path' not exist in scripts"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_path_of_scripts_not_str_type(self):
        self.__job_config["scripts"] = {"path": 111, "config_file": "ssss"}
        self.assertRaises(TypeError, validate_job_config, self.__job_config)

        err_msg = "Expect 'path' type: <class 'str'>, " \
                  "but got: <class 'int'> in scripts"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_config_file_of_scripts_not_exist(self):
        self.__job_config["scripts"] = {"path": "ssss"}
        self.assertRaises(ValueError, validate_job_config, self.__job_config)

        err_msg = "Required key: 'config_file' not exist in scripts"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_config_file_of_scripts_not_str_type(self):
        self.__job_config["scripts"] = {"path": "sss", "config_file": 111}
        self.assertRaises(TypeError, validate_job_config, self.__job_config)

        err_msg = "Expect 'config_file' type: <class 'str'>, " \
                  "but got: <class 'int'> in scripts"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_hyper_parameters_not_dict_type(self):
        self.__job_config["hyper_parameters"] = 'sss'
        self.assertRaises(TypeError, validate_job_config, self.__job_config)

        err_msg = "Expect 'hyper_parameters' type: <class 'dict'>, " \
                  "but got: <class 'str'> in job"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_max_round_num_not_int_type(self):
        self.__job_config["hyper_parameters"] = {"max_round_num": "1"}
        self.assertRaises(TypeError, validate_job_config, self.__job_config)

        err_msg = "Expect 'max_round_num' type: <class 'int'>, " \
                  "but got: <class 'str'> in hyper_parameters"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_client_num_not_int_type(self):
        self.__job_config["hyper_parameters"] = {"client_num": "1"}
        self.assertRaises(TypeError, validate_job_config, self.__job_config)

        err_msg = "Expect 'client_num' type: <class 'int'>, " \
                  "but got: <class 'str'> in hyper_parameters"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_threshold_client_num_not_int_type(self):
        self.__job_config["hyper_parameters"] = {"threshold_client_num": "1"}
        self.assertRaises(TypeError, validate_job_config, self.__job_config)

        err_msg = "Expect 'threshold_client_num' type: <class 'int'>, " \
                  "but got: <class 'str'> in hyper_parameters"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_evaluate_interval_not_int_type(self):
        self.__job_config["hyper_parameters"] = {"evaluate_interval": "1"}
        self.assertRaises(TypeError, validate_job_config, self.__job_config)

        err_msg = "Expect 'evaluate_interval' type: <class 'int'>, " \
                  "but got: <class 'str'> in hyper_parameters"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_save_interval_not_int_type(self):
        self.__job_config["hyper_parameters"] = {"save_interval": "1"}
        self.assertRaises(TypeError, validate_job_config, self.__job_config)

        err_msg = "Expect 'save_interval' type: <class 'int'>, " \
                  "but got: <class 'str'> in hyper_parameters"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_round_timeout_not_int_type(self):
        self.__job_config["hyper_parameters"] = {"round_timeout": "1"}
        self.assertRaises(TypeError, validate_job_config, self.__job_config)

        err_msg = "Expect 'round_timeout' type: <class 'int'>, " \
                  "but got: <class 'str'> in hyper_parameters"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_learning_rate_not_float_type(self):
        self.__job_config["hyper_parameters"] = {"learning_rate": 1}
        self.assertRaises(TypeError, validate_job_config, self.__job_config)

        err_msg = "Expect 'learning_rate' type: <class 'float'>, " \
                  "but got: <class 'int'> in hyper_parameters"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_ssl_not_str_type(self):
        self.__job_config["ssl"] = 1
        self.assertRaises(TypeError, validate_job_config, self.__job_config)

        err_msg = "Expect 'ssl' type: <class 'str'>, " \
                  "but got: <class 'int'> in job"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_secure_algorithm_not_dict_type(self):
        self.__job_config["secure_algorithm"] = 'sss'
        self.assertRaises(TypeError, validate_job_config, self.__job_config)

        err_msg = "Expect 'secure_algorithm' type: <class 'dict'>, " \
                  "but got: <class 'str'> in job"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_sec_algorithm_type_not_str(self):
        sec_algorithm = {"type": "sss",
                         "noise_multiplier": 1.0,
                         "adding_same_noise": True}
        self.__job_config["secure_algorithm"] = sec_algorithm
        self.assertRaises(ValueError, validate_job_config, self.__job_config)

        err_msg = "Secure algorithm: sss is not supported, " \
                  "support algorithm is ['DP', 'SSA']."
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_sec_algorithm_type_not_exist(self):
        sec_algorithm = {"noise_multiplier": 1.0,
                         "adding_same_noise": True}
        self.__job_config["secure_algorithm"] = sec_algorithm
        self.assertRaises(ValueError, validate_job_config, self.__job_config)

        err_msg = "Required key: 'type' not exist in secure_algorithm"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_dp_noise_multiplier_not_exist(self):
        sec_algorithm = {"type": "dp",
                         "adding_same_noise": True}
        self.__job_config["secure_algorithm"] = sec_algorithm
        self.assertRaises(ValueError, validate_job_config, self.__job_config)

        err_msg = "Required key: 'noise_multiplier' not exist in secure_algorithm"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_dp_noise_multiplier_not_float_type(self):
        sec_algorithm = {"type": "dp",
                         "noise_multiplier": 1,
                         "adding_same_noise": True}
        self.__job_config["secure_algorithm"] = sec_algorithm
        self.assertRaises(TypeError, validate_job_config, self.__job_config)

        err_msg = "Expect 'noise_multiplier' type: <class 'float'>, " \
                  "but got: <class 'int'> in secure_algorithm"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_dp_adding_same_noise_not_bool_type(self):
        sec_algorithm = {"type": "dp",
                         "noise_multiplier": 1.0,
                         "adding_same_noise": "true"}
        self.__job_config["secure_algorithm"] = sec_algorithm
        self.assertRaises(TypeError, validate_job_config, self.__job_config)

        err_msg = "Expect 'adding_same_noise' type: <class 'bool'>, " \
                  "but got: <class 'str'> in secure_algorithm"
        self.__check_err_msg(err_msg)

    def test_use_ssa_when_onemask(self):
        sec_algorithm = {"type": "ssa",
                         "mode": "onemask",
                         "threshold": 2}
        hyper_parameters = {
            "client_num": 3,
            "threshold_client_num": 3
        }
        self.__job_config["secure_algorithm"] = sec_algorithm
        self.__job_config["hyper_parameters"] = hyper_parameters
        self.assertRaises(ValueError, validate_job_config, self.__job_config)

        err_msg = ("When use onemask, threshold in SSA config must == "
                   "threshold_client_num and client_num in hyper_parameters")
        self.__check_err_msg(err_msg)

        sec_algorithm["threshold"] = 5
        self.assertRaises(ValueError, validate_job_config, self.__job_config)

        err_msg = ("Threshold in SSA config must <= threshold_client_num in "
                   "hyper_parameters")
        self.__check_err_msg(err_msg)

    def test_use_ssa_when_doublemask(self):
        sec_algorithm = {"type": "ssa",
                         "mode": "abc",
                         "threshold": 2}
        self.__job_config["secure_algorithm"] = sec_algorithm
        self.assertRaises(ValueError, validate_job_config, self.__job_config)

        err_msg = ("Mode for SSA must be in (onemask, doublemask), recommend"
                   " onemask used in cross-silo, doublemask used in cross-device.")
        self.__check_err_msg(err_msg)

        sec_algorithm = {"type": "ssa",
                         "mode": "doublemask",
                         "threshold": 2}
        hyper_parameters = {
            "client_num": 6,
            "threshold_client_num": 6
        }
        self.__job_config["secure_algorithm"] = sec_algorithm
        self.__job_config["hyper_parameters"] = hyper_parameters
        self.assertRaises(ValueError, validate_job_config, self.__job_config)

        err_msg = ("Threshold in SSA config must be larger than half client_num"
                   " when use ssa, this will be more secure")
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_cpu_value_not_effective(self):
        resource = {"cpu": -0.1}
        self.__job_config["resource"] = resource

        self.assertRaises(ValueError, validate_job_config, self.__job_config)

        err_msg = "Param cpu: -0.1 not effective, should greater than 0."
        self.__check_err_msg(err_msg)

    def test_check_mpc(self):
        # TODO
        pass

    def test_check_extenders(self):
        # TODO
        pass

    def test_check_parameters(self):
        # TODO
        pass


class ValidateHeartBeatTest(unittest.TestCase):

    def setUp(self) -> None:
        self.__heartbeat = {
            "id": "fl_job",
            "namespace": "fl",
            "state": "RUNNING",
            "reason": "",
            "progress": 80
        }

    def __check_err_msg(self, correct_err_msg):
        try:
            validate_heartbeat(self.__heartbeat)
        except (ValueError, TypeError) as error:
            self.assertEqual(str(error),
                             correct_err_msg)

    def test_check_heartbeat_successfully(self):
        validate_heartbeat(self.__heartbeat)

    def test_raise_exception_if_id_not_str(self):
        self.__heartbeat["id"] = 1
        self.assertRaises(TypeError, validate_heartbeat, self.__heartbeat)

        err_msg = "Expect 'id' type: <class 'str'>, " \
                  "but got: <class 'int'> in heartbeat"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_id_not_exist(self):
        del self.__heartbeat["id"]
        self.assertRaises(ValueError, validate_heartbeat, self.__heartbeat)

        err_msg = "Required key: 'id' not exist in heartbeat"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_namespace_not_str(self):
        self.__heartbeat["namespace"] = 1
        self.assertRaises(TypeError, validate_heartbeat, self.__heartbeat)

        err_msg = "Expect 'namespace' type: <class 'str'>, " \
                  "but got: <class 'int'> in heartbeat"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_namespace_not_exist(self):
        del self.__heartbeat["namespace"]
        self.assertRaises(ValueError, validate_heartbeat, self.__heartbeat)

        err_msg = "Required key: 'namespace' not exist in heartbeat"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_state_not_str(self):
        self.__heartbeat["state"] = 1
        self.assertRaises(TypeError, validate_heartbeat, self.__heartbeat)

        err_msg = "Expect 'state' type: <class 'str'>, " \
                  "but got: <class 'int'> in heartbeat"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_state_not_exist(self):
        del self.__heartbeat["state"]
        self.assertRaises(ValueError, validate_heartbeat, self.__heartbeat)

        err_msg = "Required key: 'state' not exist in heartbeat"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_state_not_supported_value(self):
        self.__heartbeat["state"] = "TEST"
        self.assertRaises(ValueError, validate_heartbeat, self.__heartbeat)

        err_msg = "State: TEST not in correct states: " \
                  "['QUEUING', 'STARTING', 'RUNNING', 'FINISHED', " \
                  "'FAILED', 'DELETING', 'STOPPING', 'STOPPED', 'PENDING']"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_reason_not_str(self):
        self.__heartbeat["reason"] = 1
        self.assertRaises(TypeError, validate_heartbeat, self.__heartbeat)

        err_msg = "Expect 'reason' type: <class 'str'>, " \
                  "but got: <class 'int'> in heartbeat"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_progress_not_int(self):
        self.__heartbeat["progress"] = "80"
        self.assertRaises(TypeError, validate_heartbeat, self.__heartbeat)

        err_msg = "Expect 'progress' type: <class 'int'>, " \
                  "but got: <class 'str'> in heartbeat"
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_progress_not_in_correct_range(self):
        self.__heartbeat["progress"] = 101
        self.assertRaises(ValueError, validate_heartbeat, self.__heartbeat)

        err_msg = "Progress: 101 must in range 0~100."
        self.__check_err_msg(err_msg)

    def test_raise_exception_if_progress_not_exist(self):
        del self.__heartbeat["progress"]
        self.assertRaises(ValueError, validate_heartbeat, self.__heartbeat)

        err_msg = "Required key: 'progress' not exist in heartbeat"
        self.__check_err_msg(err_msg)


class ValidateRequiredEnv(unittest.TestCase):

    # TODO
    pass


if __name__ == '__main__':
    unittest.main()
