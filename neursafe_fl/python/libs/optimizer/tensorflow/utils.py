#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
utils for algorithm, variables operate.
"""


def add_variables(var1, var2):
    """Add two weight list.
    """
    assert len(var1) == len(var2)
    sum_val = []

    for i, _ in enumerate(var1):
        sum_val.append(var1[i] + var2[i])
    return sum_val


def subtract_variables(var1, var2):
    """Subtract two weight list.
    """
    assert len(var1) == len(var2)
    sub_val = []
    for i, _ in enumerate(var1):
        sub_val.append(var1[i] - var2[i])
    return sub_val


def multiply(variable, constant):
    """Multiply a weight list or variable to a constant.
    """
    if isinstance(variable, list):
        return [val * constant for val in variable]
    return variable * constant


def divide(variable, constant):
    """Divide a weight list or variable with constant.
    """
    if constant == 0:
        raise ZeroDivisionError
    if isinstance(variable, list):
        return [val / constant for val in variable]
    return variable / constant
