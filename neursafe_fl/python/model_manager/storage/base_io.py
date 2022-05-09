#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
The interface of backend storage.
"""

import abc


class StorageInterface:
    """IO interface class
    """

    @abc.abstractmethod
    def copy(self, src, target, callback=None):
        """Copy src to target.
        """

    @abc.abstractmethod
    def delete(self, target, callback=None):
        """Delete the target.
        """


class StorageError(Exception):
    """Storage operate exception
    """


class PathNotExist(Exception):
    """The file or directory is not exist
    """
