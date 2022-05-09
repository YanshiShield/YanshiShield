#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=broad-except, too-many-arguments
"""subcommmand of update job.
"""

import sys

from absl import logging
import click
from neursafe_fl.python.cli.core.context import PASS_CONTEXT, LOG_FILE
from neursafe_fl.python.cli.core.data_client import DataClient
from neursafe_fl.python.cli.core.file_io import read_json_file
from neursafe_fl.python.cli.core.job import Job
from neursafe_fl.python.cli.core.upload_helper import upload_model_path, \
    upload_train_scripts_path, upload_extender_script_path, \
    init_job_use_workspace


@click.group("update", short_help="Used to update job.")
def cli():
    """Update job command."""


@cli.command("job", short_help="update job.")
@click.argument("namespace")
@click.option("-f", "--job-config-path", required=False,
              type=click.Path(exists=True, readable=True),
              help=("The config path for job, a json config."))
@click.option("-m", "--model-path", required=False, default=None,
              type=click.Path(exists=True, readable=True, resolve_path=True,
                              file_okay=True),
              help=("The config for model_path. If it is set, the model will"
                    "be uploaded to the server and then used as the initial "
                    "model for training. If there is a model_path field in "
                    "job_config, upload it to that path, otherwise upload it"
                    " to the root path, with the same file name, and "
                    "automatically fill in the model_path in job_config."))
@click.option("-s", "--scripts-path", required=False, default=None,
              type=click.Path(exists=True, readable=True, resolve_path=True,
                              dir_okay=True),
              help=("The scripts path, contain train/evalueate scripts and "
                    "entry config. If it is set, all file "
                    "in path will be uploaded to the server and then used "
                    " to run train and evaluate. If there is a scripts.path "
                    "field in job_config, upload it to that path, otherwise "
                    "upload it to the root path, with the same directory name,"
                    " and automatically fill in the scripts.path in "
                    "job_config."))
@click.option("-e", "--extender-script_path", required=False, default=None,
              type=click.Path(exists=True, readable=True, resolve_path=True,
                              file_okay=True),
              help=("The extender's script_path for running user-defined "
                    "train and aggregate. If it is set, the script file "
                    "will be uploaded to the server and then used it to run"
                    " user-defined federated learning. If there is a "
                    "extender.script_path field in job_config, upload it to"
                    " that path, otherwise upload it to the root path, "
                    "with the same file name, and automatically fill in"
                    " the extender.script_path in job_config."))
@click.option("-w", "--workspace", required=False, default=None,
              type=click.Path(exists=True, readable=True, resolve_path=True,
                              file_okay=True),
              help=("Use workspace to update job, in workspace should have: "
                    " file config.json and directory model/scripts/extender."
                    ))
@PASS_CONTEXT
def update_job(ctx, extender_script_path, scripts_path,
               model_path, job_config_path, workspace, namespace):
    """update job.

    \b
    We support use workspace(-w) to update job, in workspace should have:
        config.json: required, the job config.
        model: required, the init model or weights should in the path.
        scripts: the script which wille be send to client.
        extender: use to run user-defined train and aggregate.
    other, we also support -f/-m/-s/-e to update job config separately.
    /f
    """
    try:
        data_client = DataClient(ctx.get_data_server(), ctx.get_user(),
                                 ctx.get_password(),
                                 ctx.get_certificate_path())

        fl_job = Job(ctx.get_api_server())
        if workspace:
            job_config = init_job_use_workspace(data_client, namespace,
                                                workspace)
        else:
            job_config = read_json_file(job_config_path)
            if model_path:
                upload_model_path(data_client, namespace, model_path,
                                  job_config)
            if scripts_path:
                upload_train_scripts_path(data_client, namespace, scripts_path,
                                          job_config)
            if extender_script_path:
                upload_extender_script_path(data_client, namespace,
                                            extender_script_path, job_config)

        click.echo("")
        click.echo("start update job")
        fl_job.update(namespace, job_config)
        click.echo("update job success.")
    except Exception as err:
        logging.exception(str(err))
        click.echo("Error message: %s, the detail see %s" % (
            str(err), LOG_FILE))
        sys.exit(1)
