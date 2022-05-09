#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""File helper
"""

import json


def read_json_file(filename):
    """Read a file as json.

    Args:
        filename: the file path to read. If the file is not json file,
            will raise exception.

    Return:
        A dict, data from read the file.
    """
    with open(filename, 'r') as cfg_file:
        value = cfg_file.read()
        config_info = json.loads(value)

    return config_info


def write_json_file(filename, context):
    """Write content to json file.

    Args:
        filename: The content will write to this file.
        context: Will be wrote to file, must be a dict.
    """
    with open(filename, 'w') as cfg_file:
        cfg_file.write(json.dumps(context))
