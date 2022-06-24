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


@click.group("create", short_help="Create federated job or model.")
def cli():
    """
     Create job or model. \n
     Run 'nsfl-ctl create COMMAND --help' for more information on sub-commands.
    """


@cli.command("job", short_help="Create job.")
@click.argument("namespace")
@click.option("-f", "--job-config-path", required=False,
              type=click.Path(exists=True, readable=True),
              help=("Local path points to job config file, which used to"
                    " configure how to train the fl model, and the format is"
                    " json file."
                    " Job config typically include job name, runtime,"
                    " hyper parameters, etc. reference for details of each"
                    " parameter explanation: "
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
              help=("Use workspace to init job, you can organize all your"
                    " initial files with the following format in a workspace"
                    " directory: \n"
                    "\n  -config.json  file, refer to <job-config-path>\n"
                    "\n  -model/  dir, refer to <model-path>\n"
                    "\n  -scripts/  dir, refer to <scripts-path>\n"
                    "\n  -extender/ dir, refer to <extender-script_path>"
                    ))
@PASS_CONTEXT
def create_job(ctx, extender_script_path, scripts_path,
               model_path, job_config_path, workspace, namespace):
    """Create federated job.

    \b
    Use config files to create your federated job. Typically including four
    types of files:

     \b
        config.json: required, the job config.
        model: required, the init model or weights.
        scripts: optional, the script which will be send to client.
        extender: optional, use to run user-defined train and aggregate.

    \b
    You can use <workspace(-w)> option to init job one-time, also, you can use
     <-f/-m/-s/-e> options to initialize job separately.
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
              help="The runtime of this model, this is required, we current"
                   " support [tf, torch].")
@click.option("-l", "--local-model", required=False,
              type=click.Path(exists=True, readable=True, resolve_path=True),
              help="The path of local model file, currently we support model"
                   " file suffixed with [.pt, .pth, .h5].")
@click.option("-r", "--remote-model", required=False,
              help="The remote path of model, the path in the data server. "
                   "the format of this args should write as"
                   " 'namespace:/path/model' .")
@click.option("-v", "--version", required=False,
              help="The version(tag) of this model. If not specify the model"
                   " version, the version will be generated by server with"
                   " increased number, such as V1, V2.")
@click.option("-d", "--description", required=False,
              help="Add some description of this model.")
@PASS_CONTEXT
def create_model(ctx, description, version, remote_model,
                 local_model, runtime, name, namespace):
    """
    \b
    Create federated model, which actually means publish your model to model
     store component for federated learning. You can create with your local
     model file or the remote model file(already in the store).

    \b
    If you use your local model file, then it will be uploaded to the model
     store.
    If you use the remote model file, it will be copied to corresponding path in
     the model store.

    For example, create a tf model with local file to the default namespace
     with name mnist: \n
        nsfl-ctl create model default mnist -r tf -l /root/init.h5

    After created, each model will have a unique id, you can use the id in the
     fl job config to reference it for training.
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
