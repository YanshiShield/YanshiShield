#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Entry of Data Server.
"""
import logging
from wsgidav.fs_dav_provider import FilesystemProvider
from wsgidav.wsgidav_app import WsgiDAVApp
from wsgidav.util import init_logging
from cheroot import wsgi

import neursafe_fl.python.data_server.const as const
from neursafe_fl.python.data_server.config import DEFAULT_CONFIG
from neursafe_fl.python.utils.s3_conversion import convert_s3_to_posix


logger = logging.getLogger("wsgidav")
logger.propagate = True
logger.setLevel(const.LOG_LEVEL)


def _convert_to_verbose(log_level):
    verbose_map = {"CRITICAL": 0,
                   "ERROR": 1,
                   "WARNING": 2,
                   "INFO": 3,
                   "DEBUG": 4}
    if log_level not in verbose_map.keys():
        log_level = "DEBUG"
    return verbose_map[log_level]


def main():
    """
    Data Server Entry.
    """
    if const.STORAGE_TYPE.lower() == "s3":
        convert_s3_to_posix(const.WORKSPACE_BUCKET, const.S3_ENDPOINT,
                            const.S3_ACCESS_KEY, const.S3_SECRET_KEY,
                            const.WORKSPACE)

    provider = FilesystemProvider(const.WORKSPACE)

    config = DEFAULT_CONFIG.copy()
    config.update({
        "host": const.SERVER_ADDRESS,
        "port": const.PORT,
        "verbose": _convert_to_verbose(const.LOG_LEVEL),
        "provider_mapping": {"/": provider},
        "simple_dc": {
            "user_mapping": {
                "/": {
                    const.ACCESS_USER: {
                        "password": const.ACCESS_PASSWORD,
                        "description": "Data Server Authentication.",
                        "roles": []}}}}})

    init_logging(config)

    app = WsgiDAVApp(config)

    server_args = {
        "bind_addr": (config["host"], config["port"]),
        "wsgi_app": app
    }
    server = wsgi.Server(**server_args)

    server.start()


if __name__ == '__main__':
    main()
