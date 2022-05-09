#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=broad-except
"""subcommmand of helath check.
"""

import sys

from absl import logging
import click

from neursafe_fl.python.cli.core.context import PASS_CONTEXT, LOG_FILE
from neursafe_fl.python.cli.core.data_client import DataClient
from neursafe_fl.python.cli.core.job import Job


@click.command("health", short_help=("Health check for api "
                                     "server and datas erver."))
@PASS_CONTEXT
def cli(ctx):
    """Health check."""
    try:
        cmd_config = ctx.get_config()
        fl_job = Job(cmd_config["api_server"])
        fl_job.check_health()
        click.echo("api server ok.\n")
    except Exception as err:
        logging.exception(str(err))
        click.echo("Error message: %s, the detail see %s" % (
            str(err), LOG_FILE))
        sys.exit(1)

    try:
        data_client = DataClient(ctx.get_data_server(), ctx.get_user(),
                                 ctx.get_password(),
                                 ctx.get_certificate_path())
        data_client.list_namespaces()
        click.echo("data server ok.")
    except Exception as err:
        logging.exception(str(err))
        click.echo("Error message: %s, the detail see %s" % (
            str(err), LOG_FILE))
        sys.exit(1)
