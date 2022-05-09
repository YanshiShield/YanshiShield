#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""FL executer errors.
"""


class FLError(Exception):
    """Federate learning exception.
    """


class TaskTimeoutError(FLError):
    """When task run timeout, raise this exception.
    """


class TaskRunError(FLError):
    """Task run error.
    """
