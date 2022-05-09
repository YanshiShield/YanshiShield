#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""FL SDK for custom defined procedure.
"""

from neursafe_fl.python.client.workspace.custom import read_prepared_file, \
    read_prepared_parameters, write_result_parameter, write_result_parameters, \
    write_result_file
from neursafe_fl.python.sdk.utils import get_task_workspace


def get_parameter(key):
    """Get parameter from server.

    The parameter defined in coordinator extender, which is user custom.
    coordinator will send them to client. and user can get these parameters
    through this interface.

    Args:
        key: The parameter's key.

    Returns:
        A value is related to Key, return None if not exist.

    Raises:
        SomeException: jj


    """
    task_workspace = get_task_workspace()
    params = read_prepared_parameters(task_workspace)
    if params:
        return params.get(key, None)
    return None


def get_parameters():
    """Get all parameters from server.

    The parameters defined in coordinator extender, which is user custom.
    coordinator will send them to client. and user can get these parameters
    through this interface.

    Return:
        A dict, contain all parameters from server.
    """
    task_workspace = get_task_workspace()
    return read_prepared_parameters(task_workspace)


def put_parameter(key, value):
    """Put parameter to server.

    The Parameter will be generated in task, and this parameter will be
    send to server, used in coordinator extender for user defined aggregation.
    Note that using this will append the parameter to old parameters written
    by calling put_parameter and put_parameters above.

    Args:
        Key: parameter's key.
        Value: parameter's value.
    """
    task_workspace = get_task_workspace()
    write_result_parameter(task_workspace, key, value)


def put_parameters(parameters):
    """Put parameters to server.

    The Parameters will be generated in task, and these parameters will be
    send to server, used in coordinator extender for user defined aggregation.
    Note that using this will use parameters overwrite all the old parameters
    written by calling put_parameter and put_parameters above.

    Args:
        parameters: A dict included all parameters to send.
    """
    task_workspace = get_task_workspace()
    write_result_parameters(task_workspace, parameters)


def get_file(filename, dserialize_func=None, **kwargs):
    """Get file from server.

    The files defined in coordinator extender, which is user custom.
    coordinator will send these files to client. and user can get these
    files by filename through this interface.

    Args:
        filename: Get the file's content according to this name.
        dserialize_func: If read file's content use custom's deserialize
                         function, set it.
        kwargs: the dserialize_func's arguments.

    Return:
        File's content.
    """
    task_workspace = get_task_workspace()
    return read_prepared_file(task_workspace, filename,
                              dserialize_func, **kwargs)


def put_file(filename, content, serialize_func=None, **kwargs):
    """Put file to server.

    The files will be generated in task, and these files will be send to
    server, used in coordinator extender for user defined aggregation.

    Args:
        filename: Set file name.
        content: File's content.
        serialize_func: If serialize file's content use custom's serialize
                         function, set it.
        kwargs: the serialize_func's arguments.
    """
    task_workspace = get_task_workspace()
    write_result_file(task_workspace, filename, content,
                      serialize_func, **kwargs)
