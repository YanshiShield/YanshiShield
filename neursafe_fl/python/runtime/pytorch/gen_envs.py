# -*- coding: utf-8 -*-
"""
Generate specific environments variables about pytorch runtime
"""


#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

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
        environment variable.According to pytorch runtime, generate specific
        environment variables.
    """
    workers_envs = {}

    workers_num = len(worker_addresses)
    master_addr = None
    master_port = None

    for worker_id, worker_address in worker_addresses.items():
        if worker_address["index"] == 0:
            master_addr = worker_address["ip"]
            master_port = str(worker_address["port"])

        envs = {"WORKER_INDEX": str(worker_address["index"]),
                "WORLD_SIZE": str(workers_num),
                "RANK": str(worker_address["index"]),
                "MASTER_ADDR": master_addr,
                "MASTER_PORT": master_port}
        workers_envs[worker_id] = envs

    return workers_envs
