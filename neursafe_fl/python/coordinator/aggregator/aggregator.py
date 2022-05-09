#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Aggregator Module
"""

import abc


class Aggregator:
    """Base Aggregator Class

    Aggregator is used to process the updates(or training result) from the
    client. Aggregator is a stateful object, mainly two things:
        1. First, it will accumulate the data in args each time call the
        'accumulate' function.
        2. Second, once call the 'aggregate' function, it will calculate the
        aggregated(average) value of all the values accumulated yet.

    If you want implement a custom aggregation algorithm, you should inherit
    this class and implement two abstract functions below.
    """

    @abc.abstractmethod
    def accumulate(self, data, weight=None):
        """Accumulate data, such as metrics, weights."""

    @abc.abstractmethod
    async def aggregate(self):
        """Aggregate the accumulated data, such as calculate average."""


def aggregator_factory(aggregator_name):
    """Create aggregator according to the config

    If config is not specified, default aggregator is 'FedAvg', which is
    weight-mean aggregator.
    Also support custom aggregator, the custom aggregator will be loaded
    via name reflecting. Please make sure the custom aggregator file name
    correspond to the class name.

    For example:
            average_aggregator.py  <->  AverageAggregator

    Finally, config the name 'average_aggregator' in the config file.
    """
    import_path = 'fl.python.coordinator.aggregator.%s' % aggregator_name
    words = [word.capitalize() for word in aggregator_name.split("_")]
    class_name = "".join(words)
    aggregator = __import__(import_path, fromlist=True)
    return getattr(aggregator, class_name)
