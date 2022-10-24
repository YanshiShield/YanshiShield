#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Define support runtime and create various runtime for federated learning.
"""

import os

from enum import Enum

from neursafe_fl.python.utils.file_io import list_all_subpath


class Runtime(Enum):
    """Support runtime type.
    """
    TENSORFLOW = 'tensorflow'
    PYTORCH = 'pytorch'


class ModelRuntimeError(RuntimeError):
    """When load not supported runtime, will raise this error.
    """


def _get_support_runtime():
    runtime_path = os.path.dirname(__file__)
    subpaths = list_all_subpath(runtime_path)
    for subpath in subpaths.copy():
        if subpath.startswith('__'):
            # maybe have __pycache__, remove it.
            subpaths.remove(subpath)
    return subpaths


SUPPORT_RUNTIME = _get_support_runtime()


def _check_runtime(runtime):
    """check runtime validation"""
    if runtime not in SUPPORT_RUNTIME:
        raise ModelRuntimeError('Not support runtime: %s, the support is %s.'
                                % (runtime, SUPPORT_RUNTIME))


class RuntimeFactory:
    """Runtime factory, used to create different runtime.
    """
    @classmethod
    def create_model(cls, runtime, **kwargs):
        """Create different models according to runtime.
        """
        _check_runtime(runtime)
        model_name = 'neursafe_fl.python.runtime.%s.model' % runtime.lower()
        class_name = '%sModel' % runtime.capitalize()
        return cls._get_obj(model_name, class_name, **kwargs)

    @classmethod
    def create_weights_calculator(cls, runtime):
        """Create different weights calculator according to runtime.
        """
        _check_runtime(runtime)
        model_name = 'neursafe_fl.python.runtime.%s.weights' % runtime.lower()
        class_name = '%sWeightsCalculator' % runtime.capitalize()
        return cls._get_obj(model_name, class_name)

    @classmethod
    def create_weights_converter(cls, runtime):
        """Create different weights converter according to runtime.
        """
        _check_runtime(runtime)
        model_name = 'neursafe_fl.python.runtime.%s.weights' % runtime.lower()
        class_name = '%sWeightsConverter' % runtime.capitalize()
        return cls._get_obj(model_name, class_name)

    @classmethod
    def create_security_algorithm(cls, runtime, **kwargs):
        """Create different security algorithm to protect weights
        according to runtime.
        """
        _check_runtime(runtime)
        model_name = 'neursafe_fl.python.runtime.%s.%s' % (
            runtime.lower(), kwargs['secure_algorithm']['type'].lower())
        class_name = '%s%s' % (runtime.capitalize(),
                               kwargs['secure_algorithm']['type'].upper())
        return cls._get_obj(model_name, class_name, **kwargs)

    @classmethod
    def gen_distributed_env_vars(cls, runtime, **kwargs):
        """Generate environment variables

        Generate environment variables for every worker in multi workers
        distributed training scene.

        Args:
            runtime: deep learning framework, such as: tensorflow, pytorch
            worker_addresses: a dict about workers address info, it describe
            address and port about every worker,for example:
                {"worker_id_1": {"ip": "10.0.0.1",
                                 "port": "8080",
                                 "index": 0},
                ....}

        Returns:
            environment variables: a dict which dict key is worker id, dict
            value is still a dict, its key is environment variable key, its
            value is environment variable.According to different runtime,
            generate specific environment variables.
        """
        _check_runtime(runtime)
        model_name = 'neursafe_fl.python.runtime.%s.gen_envs' % runtime.lower()
        function_name = "gen_distributed_envs"
        return cls._get_obj(model_name, function_name, **kwargs)

    @classmethod
    def _get_obj(cls, model_name, class_name, **kwargs):
        model = __import__(model_name, fromlist=True)
        return getattr(model, class_name)(**kwargs)
