#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=broad-except
"""subcommmand of stop job.
"""

import sys

from absl import logging
import click

from neursafe_fl.python.cli.core.context import PASS_CONTEXT, LOG_FILE
from neursafe_fl.python.cli.core.job import Job
from neursafe_fl.python.cli.core.util import parse_job_id


@click.group("stop", short_help="Stop federated job.")
def cli():
    """
     Stop job command. \n
     Run 'nsfl-ctl stop COMMAND --help' for more information.
    """


@cli.command("job", short_help="Stop federated job.")
@click.argument("namespace")
@click.argument("job_id", required=False, default=None)
@click.option("-f", "--job-config", required=False, default=None,
              type=click.Path(exists=True, readable=True),
              help=("Local path <job-config> points to the configuration file "
                    " that used to create the federated job, which is json"
                    " format."))
@click.option("-w", "--workspace", required=False, default=None,
              type=click.Path(exists=True, readable=True),
              help=("Local path <workspace> points to the workspace/ directory"
                    " that used to create this federated job."))
@PASS_CONTEXT
def stop_job(ctx, namespace, job_id=None, job_config=None,
             workspace=None):
    """Stop the execution of federated job.

    When a federated job is executing, you can use this command to stop the
     execution. After stopped, you can use the 'start' command to start
     training again.

    For examples: \n
        nsfl-ctl stop job default job_1  \n
        nsfl-ctl stop job default -f /path/to/job_config.json \n
        nsfl-ctl stop job default -w /path/to/workspace \n
    Noting: The job_config.json or the workspace/ is the file or directory used
    to create this federated job. Please do not change the config if you
    start job this way. Otherwise, please use the job_id to start.
    """
    try:
        _id = parse_job_id(job_id, job_config, workspace)
        if not _id:
            raise ValueError("Must set job_id.")

        fl_job = Job(ctx.get_api_server())
        fl_job.stop(namespace, _id)
        click.echo("Stop job %s success, you can use "
                   "'nsfl get job' to query job status." % _id)
    except Exception as err:
        logging.exception(str(err))
        click.echo("Error message: %s, the detail see %s" % (
            str(err), LOG_FILE))
        sys.exit(1)
