#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
postgre sql client errors definition
"""


class DuplicateTable(Exception):
    """Duplicate table
    """


class UndefinedTable(Exception):
    """Undefined table
    """


class UniqueViolation(Exception):
    """Unique violation
    """
