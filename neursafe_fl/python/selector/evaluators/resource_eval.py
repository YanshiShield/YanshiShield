#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Resource Evaluator.
"""

from neursafe_fl.python.selector.evaluators.evaluator import Evaluator

Coefficient = {
    "gpu": 10,
    "cpu": 1,
    "memory": 1
}


class ResourceEvaluator(Evaluator):  # pylint: disable=too-few-public-methods
    """Evaluator score the client with client's resource.

    The resource can be gpu, cpu, memory. The evaluator will give a higher score
    for client with more resources.
    """

    def score(self, client, **kwargs):
        score = 0
        resource = client.resource
        if resource.get("gpu"):
            score += int(resource["gpu"]) * Coefficient["gpu"]
        if resource.get("cpu"):
            score += int(resource["cpu"]) * Coefficient["cpu"]
        if resource.get("memory"):
            score += self._unit(resource["memory"]) * Coefficient["memory"]

        return self.weight * score

    def _unit(self, memory):
        """TODO, Trans memory unit to GB
        """
        return memory
