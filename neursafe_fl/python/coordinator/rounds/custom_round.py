#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Custom Round Module."""

from neursafe_fl.python.coordinator.rounds.base_round import BaseRound


class CustomRound(BaseRound):
    """Custom Round Class.

    The CustomRound only process the user's custom(extender) functions.
    User has to define the broadcast extender and aggregate extender, there is
    no default process on the data.
    Typically, user can use this to implement some custom computations.
    """

    def __init__(self, config, round_id, workspace):
        super().__init__(config, round_id, workspace, None)
        self.__extenders = config.get("extenders")

    def on_prepare(self):
        pass

    async def on_broadcast(self, client):
        pass

    async def on_aggregate(self, msg, number):
        pass

    async def on_finish(self):
        pass

    async def on_stop(self, client):
        pass
