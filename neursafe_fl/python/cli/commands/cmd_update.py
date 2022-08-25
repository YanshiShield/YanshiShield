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


@click.group("update", short_help="Update federated job.")
def cli():
    """Update job command.
       Run 'nsfl-ctl update COMMAND --help' for more information.
    """


@cli.command("job", short_help="update job.")
@click.argument("namespace")
@click.option("-f", "--job-config-path", required=False,
              type=click.Path(exists=True, readable=True),
              help=("Local path points to job config file, which used to"
                    " configure how to train the fl model, and the format is"
                    " json file."
                    " Job config typically include job name, runtime,"
                    " hyper parameters, etc. reference for details of each"
                    " field explanation: "
                    " https://github.com/neursafe/federated-learning/"
                    "blob/main/docs/develop.md#job"))
@click.option("-m", "--model-path", required=False, default=None,
              type=click.Path(exists=True, readable=True, resolve_path=True,
                              file_okay=True),
              help=("Local path <model_path> points to the initial fl model"
                    " file for training. Current model support"
                    " [Keras, Pytorch],"
                    " correspond h5 and pth(pt) file respectively."
                    " This model file will be uploaded to the data server and"
                    " then used as the initial model for this federated job."))
@click.option("-s", "--scripts-path", required=False, default=None,
              type=click.Path(exists=True, readable=True, resolve_path=True,
                              dir_okay=True),
              help=("Local path <scripts_path> points to the directory that"
                    " contains train, evaluate scripts for the fl model,"
                    " and entrypoint, which is a json file, configuring the"
                    " path and execution of above scripts. Please refer to"
                    " our examples to learn how to write the script: \n"
                    " https://github.com/neursafe/federated-learning/tree/"
                    "main/example."
                    " The scripts in this path will be uploaded to the data"
                    " server and then broadcast to clients to run train and"
                    " evaluate process for fl model."))
@click.option("-e", "--extender-script-path", required=False, default=None,
              type=click.Path(exists=True, readable=True, resolve_path=True,
                              file_okay=True),
              help=("Local path <extender_script_path> points to the directory"
                    " that contains extender scripts, which defines the"
                    " user-defined extend functions, such as broadcast,"
                    " aggregate etc. Please refer to our examples to learn how"
                    " to write the extender scripts: \n"
                    " https://github.com/neursafe/federated-learning/tree/"
                    "main/example."
                    " The scripts in this path will be uploaded to the data"
                    " server and then integrate extensions into the default"
                    " federated learning process."))
@click.option("-w", "--workspace", required=False, default=None,
              type=click.Path(exists=True, readable=True, resolve_path=True,
                              file_okay=True),
              help=("Use workspace to init job, you can organize all your "
                    "initial files with the following format in a workspace "
                    "directory: \n"
                    "\n  -config.json  file, refer to <job-config-path>\n"
                    "\n  -model/  dir, refer to <model-path>\n"
                    "\n  -scripts/  dir, refer to <scripts-path>\n"
                    "\n  -extender/ dir, refer to <extender-script_path>"
                    ))
@PASS_CONTEXT
def update_job(ctx, extender_script_path, scripts_path,
               model_path, job_config_path, workspace, namespace):
    """Update a federated job that already exists.


    \b
    Use config files to update your federated job. Typically including four
     types of files, just like when you create the federated job:

     \b
        config.json: required, the job config.
        model: required, the init model or weights.
        scripts: optional, the script which will be send to client.
        extender: optional, use to run user-defined train and aggregate.

    \b
    You can use <workspace(-w)> option to init job one-time, also, you can use
     <-f/-m/-s/-e> options to initialize job separately.

    Under normal circumstances, after modifying the file in the original path
    where used to create the job, you can use the update operation. Be careful
    not to update the job in execution progress, you can stop it first before
    updating.
    """
    try:
        data_client = DataClient(ctx.get_data_server(), ctx.get_user(),
                                 ctx.get_password())

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
