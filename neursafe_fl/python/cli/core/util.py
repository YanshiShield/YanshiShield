#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Command util."""

import os
import errno
from neursafe_fl.python.cli.core.file_io import read_json_file

from neursafe_fl.python.cli.core.upload_helper import read_job_config


def parse_job_id(job_id, job_config, workspace):
    """Parse job id from job config."""
    if job_id is None and job_config is None and workspace is None:
        return None

    if job_id:
        return job_id

    if job_config:
        config = read_json_file(job_config)
    else:
        config = read_job_config(workspace)

    if "id" not in config:
        raise ValueError("Must set id in config file.")
    return config["id"]


def get_size(local_path):
    """Get local path file or dir size.
    """
    if os.path.isfile(local_path):
        size = os.stat(local_path).st_size
    else:
        size = _get_dir_size(local_path)

    return size


def _get_dir_size(path):
    """get local directory size
    """
    size = 0
    for root, _, files in os.walk(path):
        for file in files:
            try:
                size += os.path.getsize(os.path.join(root, file))
            except OSError as err:
                if err.errno == errno.ENOENT:
                    continue
    return size
