#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=broad-except, too-many-arguments
"""subcommmand of create job.
"""
import os
import sys
import threading

from absl import logging
import click
from neursafe_fl.python.cli.core.context import PASS_CONTEXT, LOG_FILE
from neursafe_fl.python.cli.core.data_client import DataClient
from neursafe_fl.python.cli.core.file_io import read_json_file
from neursafe_fl.python.cli.core.job import Job
from neursafe_fl.python.cli.core.model import Model
from neursafe_fl.python.cli.core.upload_helper import upload_model_path, \
    upload_train_scripts_path, upload_extender_script_path, \
    init_job_use_workspace


@click.group("create", short_help="Used to create job or model.")
def cli():
    """Create job or model command."""


@cli.command("job", short_help="Create job.")
@click.argument("namespace")
@click.option("-f", "--job-config-path", required=False,
              type=click.Path(exists=True, readable=True),
              help=("The config path for job, a json config."))
@click.option("-m", "--model-path", required=False, default=None,
              type=click.Path(exists=True, readable=True, resolve_path=True,
                              file_okay=True),
              help=("The config for model_path. If it is set, the model will"
                    "be upload to the server and then used as the initial "
                    "model for training. If there is a model_path field in "
                    "job_config, upload it to that path, otherwise upload it"
                    " to the root path, with the same file name, and "
                    "automatically fill in the model_path in job_config."))
@click.option("-s", "--scripts-path", required=False, default=None,
              type=click.Path(exists=True, readable=True, resolve_path=True,
                              dir_okay=True),
              help=("The scripts path, contain train/evalueate scripts and "
                    "entry config. If it is set, all file "
                    "in path will be upload to the server and then used "
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
                    "will be upload to the server and then used it to run"
                    " user-defined federated learning. If there is a "
                    "extender.script_path field in job_config, upload it to"
                    " that path, otherwise upload it to the root path, "
                    "with the same file name, and automatically fill in"
                    " the extender.script_path in job_config."))
@click.option("-w", "--workspace", required=False, default=None,
              type=click.Path(exists=True, readable=True, resolve_path=True,
                              file_okay=True),
              help=("Use workspace to init job, in workspace should have: "
                    " file config.json and directory model/scripts/extender."
                    ))
@PASS_CONTEXT
def create_job(ctx, extender_script_path, scripts_path,
               model_path, job_config_path, workspace, namespace):
    """Create job.

    \b
    We support use workspace(-w) to init job, in workspace should have:
        config.json: required, the job config.
        model: required, the init model or weights should in the path.
        scripts: the script which wille be send to client.
        extender: use to run user-defined train and aggregate.
    other, we also support -f/-m/-s/-e to initialize job config separately.
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
        click.echo("create job")
        fl_job.create(namespace, job_config)
        click.echo("create job success.")
    except Exception as err:
        logging.exception(str(err))
        click.echo("Error message: %s, the detail see %s" % (
            str(err), LOG_FILE))
        sys.exit(1)


@cli.command("model", short_help="Create model.")
@click.argument("namespace")
@click.argument("name")
@click.option("-t", "--runtime", required=True,
              type=click.Choice(['tf', 'torch'], case_sensitive=False),
              help="The runtime of this model, this must be declared.")
@click.option("-l", "--local_model", required=False,
              type=click.Path(exists=True, readable=True, resolve_path=True),
              help="The path of model in local disk, should be a file.")
@click.option("-r", "--remote_model", required=False,
              help="The remote path of model, the path in the data server. "
                   "the format of this args should write as"
                   " 'namespace:/path/model' .")
@click.option("-v", "--version", required=False,
              help="The version(tag) of model.")
@click.option("-d", "--description", required=False,
              help="Add some description of this model.")
@PASS_CONTEXT
def create_model(ctx, description, version, remote_model,
                 local_model, runtime, name, namespace):
    """Create model.

    \b
    Create model, also namely publish model to model store for federate
    learning. You can use your local model file or the remote model file to
    create. The local model will be uploaded, and the remote model will be copy
    to model store. \b
    If not specify the model version, the version will be generated.
    After created, each model has a unique id, you can use the id in the fl job
    config for training.
    """
    try:
        config = {
            "name": name,
            "runtime": runtime,
            "description": description
        }
        if version:
            config["version"] = version

        if remote_model:
            fl_model = Model(ctx.get_api_server())
            config["model_path"] = remote_model
            fl_model.create(namespace, config)
        else:
            _upload_model_and_create(ctx, namespace, config, local_model)

        click.echo("create model success")

    except Exception as err:
        logging.exception(str(err))
        click.echo("Error message: %s, the detail see %s" % (
            str(err), LOG_FILE))
        sys.exit(1)


def _upload_model_and_create(ctx, namespace, config, local_model):
    if os.path.isdir(local_model):
        raise Exception("Not support model is directory.")
    fl_model = Model(ctx.get_api_server())
    data_client = DataClient(ctx.get_data_server(), ctx.get_user(),
                             ctx.get_password(),
                             ctx.get_certificate_path())

    def upload_progress(progress):
        fl_model.upload_progress(model_info["id"], progress)

    reporter = ReportProgress(threading.Event(), data_client,
                              upload_progress)
    config["file_name"] = os.path.basename(local_model)
    model_info = fl_model.create(namespace, config)
    try:
        remote_storage = model_info["storage_info"]
        model_store, remote_path = remote_storage[0], remote_storage[1]

        click.echo("start upload model")
        reporter.start()
        data_client.upload_file(model_store, local_model, remote_path)
        reporter.stop()
        upload_progress({"state": "success", "progress": "100"})
    except Exception as err:
        reporter.stop()
        upload_progress({"state": "failed", "reason": str(err)})
        raise Exception from err


class ReportProgress(threading.Thread):
    """Thread used to report upload command progress.
    """
    def __init__(self, event, data_client, report_func):
        super().__init__()
        self.stopped = event
        self.report_func = report_func
        self.data_client = data_client

    def run(self):
        """Start run the thread.
        """
        while not self.stopped.wait(3):
            progress = {"state": "uploading",
                        "progress": self.data_client.progress}
            self.report_func(progress)

    def stop(self):
        """Stop the thread.
        """
        self.stopped.set()
