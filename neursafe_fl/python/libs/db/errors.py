#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
data base exception definition
"""


class DataBaseError(Exception):
    """Data Base Error
    """


class DBConnectError(DataBaseError):
    """Connect data base error"""


class DBAuthError(DataBaseError):
    """Auth data base error"""


class DBAlreadyExisting(Exception):
    """Data base already existing"""


class DBNotExisting(Exception):
    """Data base not existing"""


class CollectionAlreadyExisting(Exception):
    """Collection already existing"""


class CollectionNotExisting(Exception):
    """Collection not existing"""


class DataAlreadyExisting(Exception):
    """Data already existing"""


class DataNotExisting(Exception):
    """Data not existing"""
