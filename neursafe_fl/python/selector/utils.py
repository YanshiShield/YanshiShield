#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Util functions
"""


def split(attr, separator=","):
    """Split if it is string, otherwise do nothing.
    """
    if isinstance(attr, str):
        tmp = attr.strip(separator)
        return tmp.split(separator)
    return attr


def to_dict(proto):
    """Transform the proto to dict
    """
    tmp = {}
    for key in proto:
        tmp[key] = proto[key]
    return tmp
