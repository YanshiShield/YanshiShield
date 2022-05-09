#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Error(exception) definition"""


class NotExist(Exception):
    """Base exception of model.
    """


class ModelNotExist(NotExist):
    """The model is not exist.
    """


class ModelIDNotExist(NotExist):
    """The model id is not exist.
    """


class RequestError(Exception):
    """Client request with bad parameters.
    """


class ModelAlreadyExist(RequestError):
    """The model is already exist when create.
    """


class ModelStateError(RequestError):
    """The current model state not support operation.
    """


class ServiceException(Exception):
    """Internal service error.
    """


class StorageError(ServiceException):
    """The backend storage service error.
    """
