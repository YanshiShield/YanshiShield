#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""File helper
"""

import os
from io import BytesIO
import json
import zipfile


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


def list_all_files(path):
    """list all filenames in path, only filenames.

    Args:
        path: Will be walk in the path, list the filenames.

    Return:
        A list, list the filenames in the first level directory.
        If path not exist, return a empty list.
    """
    for _, _, filenames in os.walk(path):
        return filenames
    return []


def list_all_subpath(path):
    """list all subpaths in path, only subpaths.

    Args:
        path: Will be walk in the path, list the subpaths.

    Return:
        A list, list the subpaths in the first level directory.
        If path not exist, return a empty list.
    """
    for _, subpaths, _ in os.walk(path):
        return subpaths
    return []


def zip_files(files):
    """Zip all files to BytesIO.

    Args:
        files: [(filename_in_zip, file_path),], all files will be compress
                in a BytesIO.

    Return:
        A BytesIO file in memory, zipped all files.
    """
    bytes_io = BytesIO()
    with zipfile.ZipFile(bytes_io, 'w', zipfile.ZIP_STORED) as z_file:
        for filename_in_zip, file_path in files:
            if os.path.isdir(file_path):
                _zip_dir(file_path, filename_in_zip, z_file)
            else:
                z_file.write(file_path, filename_in_zip)
    return bytes_io


def _zip_dir(root, base_in_zip, z_file):
    for dirpath, _, filenames in os.walk(root):
        relative_path_in_zip = os.path.join(
            base_in_zip,
            *dirpath.replace(root, '').split(os.sep))
        for filename in filenames:
            z_file.write(os.path.join(dirpath, filename),
                         os.path.join(relative_path_in_zip, filename))


def unzip(file, path):
    """Unzip the file in bytes_io to path.

    Args:
        file: File path or file-like object.
        path: The path where will be uncompress.
    """
    zipfile.ZipFile(file).extractall(path)
