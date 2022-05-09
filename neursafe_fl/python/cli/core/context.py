#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""nsfl context.
"""

import logging
import os

import click

from neursafe_fl.python.cli.core.file_io import read_json_file, write_json_file


CFG_FILE = "/etc/nsfl.json"
LOG_FILE = "/var/log/nsfl.log"


def set_log(debug):
    """Set log"""
    log_level = logging.INFO
    if debug:
        log_level = logging.DEBUG
    logging.basicConfig(format=("[%(asctime)s] %(filename)s[line:%(lineno)d] "
                                "%(levelname)s: %(message)s"),
                        filename=LOG_FILE,
                        filemode="a",
                        level=log_level)


class Context:
    """Context for command."""
    def __init__(self):
        self.__home = os.getcwd()
        self.__cfg_data = {}
        self.__read_cfg()

    def __read_cfg(self):
        """Read config from config file."""
        try:
            self.__cfg_data = read_json_file(CFG_FILE)
        except IOError:
            self.__create_config_file()
            self.__cfg_data = {}
        # if CFG_FILE is blank, the return is None, then set cfg_data as {}
        if self.__cfg_data is None:
            self.__cfg_data = {}

    def __write_config(self):
        """Write new config to config file."""
        if not os.path.exists(CFG_FILE):
            os.makedirs(os.path.dirname(CFG_FILE))
        write_json_file(CFG_FILE, self.__cfg_data)

    def set_config(self, config):
        """Set config."""
        self.__cfg_data = config
        self.__write_config()

    def get_config(self):
        """Get config."""
        return self.__cfg_data

    def get_data_server(self):
        """Get data server."""
        return self.__cfg_data["data_server"]

    def get_api_server(self):
        """Get api server."""
        return self.__cfg_data["api_server"]

    def get_user(self):
        """Get username."""
        return self.__cfg_data["user"]

    def get_password(self):
        """Get user password."""
        return self.__cfg_data["password"]

    def get_certificate_path(self):
        """Get certificate path for data server."""
        try:
            result = self.__cfg_data["certificate"]
            if result.lower() == "none":
                return None
            return result
        except KeyError:
            return None

    def __create_config_file(self):
        if not os.path.exists(os.path.dirname(CFG_FILE)):
            os.makedirs(os.path.dirname(CFG_FILE))
        write_json_file(CFG_FILE, {})


PASS_CONTEXT = click.make_pass_decorator(Context, ensure=True)
