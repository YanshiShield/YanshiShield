#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
data base factory
"""

from absl import logging

from neursafe_fl.python.libs.db.mongo.mongo import MongoDB
from neursafe_fl.python.libs.db.postgre.postgre import PostgreSQL
from neursafe_fl.python.libs.db.errors import DataBaseError


class DBType:  # pylint: disable=too-few-public-methods
    """Data base type
    """
    MONGO = "mongo"
    POSTGRESQL = "postgreSQL"


def create_db(db_type, **kwargs):
    """
    Create data base

    Args:
        db_type: data base type
        kwargs: db parameters

    Returns:
        db object.

    Raises:
        DataBaseError: if some error occur.
    """
    if db_type == DBType.MONGO:
        return MongoDB(**kwargs)

    if db_type == DBType.POSTGRESQL:
        return PostgreSQL(**kwargs)

    err_msg = "No support database type: %s" % db_type
    logging.error(err_msg)
    raise DataBaseError(err_msg)
