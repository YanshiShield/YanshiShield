#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=broad-except
"""subcommmand of start job.
"""

import sys

from absl import logging
import click

from neursafe_fl.python.cli.core.util import parse_job_id
from neursafe_fl.python.cli.core.context import PASS_CONTEXT, LOG_FILE
from neursafe_fl.python.cli.core.job import Job


@click.group("start", short_help="Used to start job.")
def cli():
    """Start job command."""


@cli.command("job", short_help="Start job.")
@click.argument("namespace")
@click.argument("job_id", required=False, default=None)
@click.option("-f", "--job-config", required=False, default=None,
              type=click.Path(exists=True, readable=True),
              help=("The config path for job, a json config."))
@click.option("-w", "--workspace", required=False, default=None,
              type=click.Path(exists=True, readable=True),
              help=("The workspace for job, "
                    "there must config.json in workspace."))
@PASS_CONTEXT
def start_job(ctx, namespace, job_id=None, job_config=None,
              workspace=None):
    """Start job.
    """
    try:
        _id = parse_job_id(job_id, job_config, workspace)
        if not _id:
            raise ValueError("Must set job_id.")

        fl_job = Job(ctx.get_api_server())
        fl_job.start(namespace, _id)
        click.echo("Start job %s success, you can use "
                   "'nsfl get job' to query job status." % _id)
    except Exception as err:
        logging.exception(str(err))
        click.echo("Error message: %s, the detail see %s" % (
            str(err), LOG_FILE))
        sys.exit(1)
