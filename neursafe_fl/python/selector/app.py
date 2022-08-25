#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Selector Server EntryPoint.
"""

import os
import asyncio

from absl import app
from absl import flags
from absl import logging

from neursafe_fl.python.utils.log import set_log
from neursafe_fl.python.utils.file_io import read_json_file
from neursafe_fl.python.selector.selector import Selector
import neursafe_fl.python.selector.const as const
from neursafe_fl.python.utils.s3_conversion import convert_s3_to_posix

FLAGS = flags.FLAGS


flags.DEFINE_string("host", "0.0.0.0", "IP address to serve for gRPC API.")
flags.DEFINE_integer("port", 50055, "Port to listen on for gRPC API, the range "
                                    "is 1024~65535. Default port is 50055.",
                     lower_bound=1024, upper_bound=65535)
flags.DEFINE_string("log_level", "DEBUG",
                    "Log level, support [DEBUG, INFO, WARNING, ERROR].")
flags.DEFINE_string("auth_client", "false",
                    "Verify the legitimacy of the client. If True, the client"
                    "should send its certificate or public key. Only the"
                    "clients pass the authentication can be trained.")
flags.DEFINE_string("root_cert", None, "The root cert path, root cert to verify"
                                       "the legitimacy of client.")
flags.DEFINE_string("ssl", None,
                    "If use gRPCs, you must set the ssl path, This is a path "
                    "where should have 3 files:\n"
                    "  cert.pem: saved certificate\n"
                    "  private.key: saved private key\n"
                    "  trusted.pem: saved trusted certificate, which will be "
                    "the selector's certificate.")
flags.DEFINE_string("optimal_select", "true",
                    "Whether the client will be selected by optimal strategy. "
                    "If set False, the selector will random select client "
                    "after filter. If set True, you can config the strategy in"
                    "config file, or using the default strategy.")
flags.DEFINE_string("config_file", None,
                    "Path to the config file for selector. if not set, the"
                    "selector will use the default option to select clients.")


def _parse_config(config):
    """Parse the config file and verify the validity of the configuration.
    """
    if config["config_file"] and os.path.exists(config["config_file"]):
        user_config = read_json_file(config["config_file"])
        config.update(user_config)
        logging.info("load config file success, %s", config)
    return config


def main(argv):
    """The Entry of selector process."""
    del argv  # Unused

    config_dic = FLAGS.flag_values_dict()
    set_log(config_dic["log_level"])

    if const.STORAGE_TYPE.lower() == "s3":
        convert_s3_to_posix(const.WORKSPACE_BUCKET, const.S3_ENDPOINT,
                            const.S3_ACCESS_KEY, const.S3_SECRET_KEY,
                            const.WORKSPACE)

    logging.info("Load parameters: %s", config_dic)
    config = _parse_config(config_dic)

    selector = Selector(config)
    asyncio.run(selector.start())


if __name__ == '__main__':
    app.run(main)
