#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=eval-used

"""FL SDK const.
"""

import os
import pickle
import asyncio

from neursafe_fl.python.runtime.runtime_factory import RuntimeFactory
from neursafe_fl.python.client.executor.executor import DEFAULT_TASK_TIMEOUT
from neursafe_fl.python.libs.secure.secure_aggregate.ssa_protector import \
    SSAProtector


TASK_WORKSPACE = "NSFL_TASK_WORKSPACE"
TASK_RUNTIME = "NSFL_TASK_RUNTIME"
TASK_OPTIMIZER = "NSFL_TASK_OPTIMIZER"
DATASETS = "NSFL_DATASETS"
GRPC_METADATA = "NSFL_GRPC_METADATA"
CERTIFICATION_PATH = "NSFL_CERTIFICATE_PATH"
SECURITY_ALGORITHM = "NSFL_SECURITY_ALGORITHM"
COMPRESSION_ALGORITHM = "NSFL_COMPRESSION_ALGORITHM"
SERVER_ADDRESS = "NSFL_SERVER_ADDRESS"
TASK_METADATA = "NSFL_TASK_METADATA"
TASK_TIMEOUT = "NSFL_TASK_TIMEOUT"
SSA_SECRET_PATH = "NSFL_SSA_SECRET_PATH"


def get_task_workspace():
    """Get task workspace from env.

    When start task, the client will set TASK_WORKSPACE to env.
    """
    return os.getenv(TASK_WORKSPACE)


def get_runtime():
    """Get runtime from env.

    When start task, the client will set TASK_RUNTIME to env.
    """
    return os.getenv(TASK_RUNTIME)


def get_datasets():
    """Get datasets from env.

    When start task, the client will set DATASETS to env.
    """
    return os.getenv(DATASETS)


def get_grpc_metadata():
    """Get grpc metadata from env.
    """
    grpc_metadata = os.getenv(GRPC_METADATA)

    if grpc_metadata:
        return pickle.loads(eval(grpc_metadata))

    return {}


def get_security_algorithm():
    """Get security algorithm parameters from env.
    """
    security_algorithm = os.getenv(SECURITY_ALGORITHM)

    if security_algorithm:
        return pickle.loads(eval(security_algorithm))

    return {}


def get_compression_algorithm():
    """Get compress algorithm parameters from env.
    """
    compression_algorithm = os.getenv(COMPRESSION_ALGORITHM)

    if compression_algorithm:
        return pickle.loads(eval(compression_algorithm))

    return {}


def get_ssl_certification_path():
    """Get grpc ssl certification file path from env.
    """
    return os.getenv(CERTIFICATION_PATH)


def get_server_address():
    """Get server(coordinator) address for reporting metrics and weights.
    """
    return os.getenv(SERVER_ADDRESS)


def get_task_metadata():
    """Get task metadata from env.
    """
    task_metadata = os.getenv(TASK_METADATA)

    if task_metadata:
        return pickle.loads(eval(task_metadata))

    return {}


def get_task_timeout():
    """Get task execution timeout from env.
    """
    timeout = os.getenv(TASK_TIMEOUT)

    if timeout:
        return int(timeout)

    return DEFAULT_TASK_TIMEOUT


def get_ssa_secret_path():
    """
    Get secret file path which save secret shares info for SSA algorithm.
    """
    return os.getenv(SSA_SECRET_PATH)


def create_security_algorithm():
    """Create security algorithm for protecting delta weights.
    """
    algorithm_parameters = get_security_algorithm()
    task_timeout = get_task_timeout()
    ssa_secret_path = get_ssa_secret_path()

    ssa_protector = None
    if not algorithm_parameters:
        return None

    if algorithm_parameters["type"].lower() == "ssa":
        ssa_protector = SSAProtector(ssa_secret_path,
                                     algorithm_parameters["use_same_mask"],
                                     task_timeout)

    security_algorithm = RuntimeFactory.create_security_algorithm(
        get_runtime(),
        secure_algorithm=dict(algorithm_parameters),
        ssa_protector=ssa_protector)

    return security_algorithm


def do_function_sync(func, *args, **kwargs):
    """Run async function in sync mode.
    """
    loop = asyncio.get_event_loop()
    coroutine_ = func(*args, **kwargs)
    return loop.run_until_complete(coroutine_)
