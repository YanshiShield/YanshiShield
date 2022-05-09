#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Define errors(exceptions) for federate learning process."""


class RoundStoppedError(Exception):
    """When the stop condition configured by the user is reached."""


class RoundFailedError(Exception):
    """When round execute failed, such as timeout or clients failed."""


class AggregationFailedError(Exception):
    """When aggregate weights or metrics failed."""


class ExtendExecutionFailed(Exception):
    """When execute extender function failed."""


class DeviceNotEnoughError(Exception):
    """When required client number is more than left devices."""


class RemoteCallFailedError(Exception):
    """When call the remote services failed."""
