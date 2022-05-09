"""Data Evaluator.
"""
#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import math
from neursafe_fl.python.selector.evaluators.evaluator import Evaluator

BATCH_SIZE = 32


class DataEvaluator(Evaluator):  # pylint: disable=too-few-public-methods
    """Data Evaluator score the client with training data size.

    Typically is the total sample number of dataset that can be used for train.
    """

    def score(self, client, **kwargs):
        score = 0
        datasets = kwargs.get("data")
        if datasets:
            for dataset in datasets.split(","):
                if client.data.get(dataset):
                    sample_number = int(client.data[dataset])
                    score += math.ceil(sample_number / BATCH_SIZE)
        return self.weight * score
