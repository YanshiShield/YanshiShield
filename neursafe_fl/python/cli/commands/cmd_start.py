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


@click.group("start", short_help="Start federated job.")
def cli():
    """
     Start job command. \n
     Run 'nsfl-ctl start COMMAND --help' for more information.
    """


@cli.command("job", short_help="Start federated job.")
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
def start_job(ctx, namespace, job_id=None, job_config=None,
              workspace=None):
    """
    Start a federated job to execute. After created the federated job,
    you can use this command to start the job to execute.

    For examples: \n
        nsfl-ctl start job default job_1  \n
        nsfl-ctl start job default -f /path/to/job_config.json \n
        nsfl-ctl start job default -w /path/to/workspace \n
    Noting: The job_config.json or the workspace/ is the file or directory used
    to create this federated job. Please do not change the config if you
    start job this way. Otherwise, please use the job_id to start.

    During the execution, you can use the 'get' command to check progress, or
     use the 'stop' command stop the job execution.

    When the job execute finished, the final training model will be stored in
     model store, you can use 'model' commands to check, download the model.
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
