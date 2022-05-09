#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
Generate specific environments variables about tensorflow runtime
"""

import json


def gen_distributed_envs(worker_addresses):
    """Generate environment variables

    Generate environment variables for every worker in multi workers distributed
    training scene.

    Args:
        worker_addresses: a dict about workers address info, it describe address
        and port about every worker,for example:
            {"worker_id_1": {"ip": "10.0.0.1",
                             "port": "8080",
                             "index": 0},
            ....}

    Returns:
        environment variables: a dict which dict key is worker id, dict value is
        still a dict, its key is environment variable key, its value is
        environment variable.According to tensorflow runtime, generate specific
        environment variables.
    """
    workers_envs = {}

    addresses = []
    for _, worker_address in worker_addresses.items():
        addresses.append("%s:%s" % (worker_address["ip"],
                                    worker_address["port"]))

    for worker_id, worker_address in worker_addresses.items():
        envs = {"WORKER_INDEX": str(worker_address["index"]),
                "TF_CONFIG": _gen_tf_config(worker_address["index"], addresses)}
        workers_envs[worker_id] = envs

    return workers_envs


def _gen_tf_config(worker_index, addresses):
    tf_config = {"cluster": {"worker": addresses},
                 "task": {"index": worker_index,
                          "type": "worker"}}

    return json.dumps(tf_config)
