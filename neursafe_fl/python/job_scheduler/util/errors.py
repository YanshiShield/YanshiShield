#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
Errors for job scheduler.
"""


class JobSchedulerError(Exception):
    """
    Job scheduler base error
    """


class JobNotExist(JobSchedulerError):
    """
    job not exist
    """


class CheckpointNotExist(JobSchedulerError):
    """
    checkpoint not exist
    """


class NamespaceNotExist(JobSchedulerError):
    """
    namespace not exist
    """


class JobExist(JobSchedulerError):
    """
    job already exist
    """


class SchedulingError(JobSchedulerError):
    """
    schedule job error
    """


class CoordinatorCreateFailed(Exception):
    """
    Failed to create coordinator.
    """


class CoordinatorExists(Exception):
    """
    Failed to create coordinator.
    """


class CoordinatorDeleteFailed(Exception):
    """
    Failed to delete coordinator.
    """


class CoordinatorGetFailed(Exception):
    """Failed to get coordinator."""


class CoordinatorNotExist(Exception):
    """The coordinator does not exist."""


class RetryError(Exception):
    """
    Retry error
    """


class ModelNotExist(ValueError):
    """Model not existing"""


class NoEnoughClientsResource(Exception):
    """no enough clients resource"""
