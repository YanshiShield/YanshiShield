#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Entry of model manager.
"""
from absl import app

from neursafe_fl.python.utils.log import set_log
from neursafe_fl.python.model_manager.manager import ModelManager
from neursafe_fl.python.model_manager.http_server.server import Server
from neursafe_fl.python.model_manager.utils.const import LOG_LEVEL
import neursafe_fl.python.model_manager.utils.const as const
from neursafe_fl.python.utils.s3_conversion import convert_s3_to_posix


def main(argv):
    """The main entry of model manager.
    """
    del argv
    set_log(LOG_LEVEL)

    if const.STORAGE_TYPE.lower() == "s3":
        convert_s3_to_posix(const.WORKSPACE_BUCKET, const.S3_ENDPOINT,
                            const.S3_ACCESS_KEY, const.S3_SECRET_KEY,
                            const.WORKSPACE)

    model_manager = ModelManager()
    model_manager.start()

    # load http server and start service
    http_server = Server(model_manager)
    http_server.start()


if __name__ == "__main__":
    app.run(main)
