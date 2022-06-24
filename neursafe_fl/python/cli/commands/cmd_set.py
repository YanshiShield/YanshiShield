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


@click.group("set", short_help="Set configs to connect federated server.")
def cli():
    """Set federated server configs. \n
    Run 'nsfl-ctl set COMMAND --help' for more information.
    """


@cli.command("config", short_help="Set config.")
@click.option("-s", "--api-server", required=False, default=None,
              help="Set the api server address, with 'ip:port' format.")
@click.option("-d", "--data-server", required=False, default=None,
              help="Set the data server address, with 'ip:port' format.")
@click.option("-u", "--user", required=False, default=None,
              help="Username for login data server.")
@click.option("-p", "--password", required=False, is_flag=True,
              help="Flag to indicate whether a password is required to"
                   " login data server, if set, will prompt to input password.")
@click.option("-c", "--certificate-path", required=False, default=None,
              help="Local path points to the TLS certificate for data server."
                   " TLS(HTTPS) certificate is used for authentication for"
                   " standard S3 object storage.")
@PASS_CONTEXT
def set_config(ctx, api_server, data_server, user, password, certificate_path):
    """
    The CLI tool connects the api-server and data-server components in
    the federated services. The api-server is used to forward messages to
    internal components, and the data-server is used to upload data, such as
    model, scripts etc.

    Use this command to set the address or login info of above two components.

    For examples: \n
    set api-server address: \n
        nsfl-ctl set config -s 192.x.x.x:8080

    set user to login data-server: \n
        nsfl-ctl set config -u bob -p (there will prompt to input password)
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
