#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Evaluator Module.
"""

import abc

MAX_SCORE = 100


class Evaluator:  # pylint: disable=too-few-public-methods
    """The evaluator base class.

    Evaluator is used to score the client based on some attributes, resources
    or current status.

    Attributes:
        weight: int, the weight value of this evaluator. The score will be
                multiplied with this value.
    """

    def __init__(self, weight):
        self.weight = weight

    @abc.abstractmethod
    def score(self, client, **kwargs):
        """Score the client according the client's current state.

        Args:
            client: the client object to be scored.

        Returns:
            An int value of score.
        """
