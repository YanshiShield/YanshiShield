#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
job scheduler entry
"""

import os
from absl import app
from absl import logging

from neursafe_fl.python.utils.log import set_log
from neursafe_fl.python.job_scheduler.util.validations import \
    validate_required_env
from neursafe_fl.python.job_scheduler.http_server.server import HttpServer
from neursafe_fl.python.job_scheduler.scheduler import Scheduler
from neursafe_fl.python.utils.s3_conversion import convert_s3_to_posix
import neursafe_fl.python.job_scheduler.util.const as const


def main(argv):
    """
    Job scheduler
    """
    del argv  # Unused
    set_log(os.getenv("LOG_LEVEL", "DEBUG"))

    validate_required_env()

    if const.STORAGE_TYPE.lower() == "s3":
        convert_s3_to_posix(const.WORKSPACE_BUCKET, const.S3_ENDPOINT,
                            const.S3_ACCESS_KEY, const.S3_SECRET_KEY,
                            const.WORKSPACE)

    scheduler = Scheduler()
    scheduler.start()

    http_server = HttpServer(scheduler)
    http_server.start()

    logging.info('Job scheduler start successfully.')


if __name__ == "__main__":
    app.run(main)
