#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=broad-except, too-many-arguments
"""subcommmand of set config.
"""

import sys

from absl import logging
import click

from neursafe_fl.python.cli.core.aes import encrypt
from neursafe_fl.python.cli.core.context import PASS_CONTEXT, LOG_FILE


@click.group("set", short_help="Set config.")
def cli():
    """Set config."""


@cli.command("config", short_help="Set config.")
@click.option("-s", "--api_server", required=False, default=None,
              help="Set the api server address.")
@click.option("-d", "--data_server", required=False, default=None,
              help="Set the data server address.")
@click.option("-u", "--user", required=False, default=None,
              help="Username for login data server.")
@click.option("-p", "--password", required=False, is_flag=True,
              help="Password for login data server.")
@click.option("-c", "--certificate-path", required=False, default=None,
              help="TLS certificate path for data server.")
@PASS_CONTEXT
def set_config(ctx, api_server, data_server, user, password, certificate_path):
    """Set config.
    """
    try:
        config = ctx.get_config()
        if api_server:
            config["api_server"] = api_server
        if data_server:
            config["data_server"] = data_server
        if user:
            config["user"] = user
        if password:
            passwor_str = click.prompt("password", hide_input=True,
                                       confirmation_prompt=True)
            config["password"] = encrypt(passwor_str)
        if certificate_path:
            config["certificate"] = certificate_path

        ctx.set_config(config)
        click.echo("Set config ok.")
    except Exception as err:
        logging.exception(str(err))
        click.echo("Error message: %s, the detail see %s" % (
            str(err), LOG_FILE))
        sys.exit(1)
