#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Command util."""

import os

from absl import logging
import click
from neursafe_fl.python.cli.core.file_io import read_json_file


WORKSPACE_JOB_CONFIG = "config.json"
WORKSPACE_MODEL = "model"
WORKSPACE_SCRIPTS = "scripts"
WORKSPACE_EXTENDER = "extender"


def upload_model_path(data_client, namespace, model_path, job_config):
    """Upload model path to server.

    Args:
        data_client: The client to help upload data.
        model_path: The model which will be upload.
        job_config: Job_config[model_path] is the path will be upload to
            server. if not set model_path in job_config, the model will
            be upload to root in server, and automatically fill in
            job_config[model_path].
    """
    if not job_config.get("model_path", None):
        job_config["model_path"] = os.path.basename(model_path)
    click.echo("start upload %s to %s" % (model_path,
                                          job_config["model_path"]))
    data_client.upload_file(namespace, model_path, job_config["model_path"])
    click.echo("\nupload success.")


def upload_train_scripts_path(data_client, namespace,
                              train_script_path, job_config):
    """Upload train script path to server.

    Args:
        data_client: The client to help upload data.
        train_script_path: The train script path which will be upload.
        job_config: Job_config[script][path] is the path will be upload to
            server. if not set Job_config[script][path] in job_config,
            the script will be upload to root in server, and automatically
            fill in Job_config[script][path].
    """
    if "scripts" not in job_config:
        raise ValueError("if use -s, must set scripts in job_config.")
    if not job_config["scripts"].get("path", None):
        job_config["scripts"]["path"] = os.path.basename(train_script_path)
    click.echo("start upload %s to %s" % (train_script_path,
                                          job_config["scripts"]["path"]))
    data_client.upload_files(namespace,
                             train_script_path, job_config["scripts"]["path"])
    click.echo("\nupload success.")


def upload_extender_script_path(data_client, namespace,
                                extender_script_path, job_config):
    """Upload extender script path to server.

    Args:
        data_client: the client to help upload data.
        extender_script_path: The extender script path which will be upload.
        job_config: Job_config[extender][script_path] is the path will be
            upload to server. if not set Job_config[extender][script_path]
            in job_config, the script will be upload to root in server,
            and automatically fill in Job_config[extender][script_path].
    """
    if "extender" not in job_config:
        raise ValueError("if use -e, must set extender in job_config.")
    if not job_config["extender"].get("script_path", None):
        job_config["extender"]["script_path"] = os.path.basename(
            extender_script_path)
    click.echo("start upload %s to %s" % (
        extender_script_path, job_config["extender"]["script_path"]))
    data_client.upload_files(namespace, extender_script_path,
                             job_config["extender"]["script_path"])
    click.echo("\nupload success.")


def parse_job_id(job_id, job_config, workspace):
    """Parse job id from job config."""
    if job_id is None and job_config is None and workspace is None:
        return None

    if job_id:
        return job_id

    if job_config:
        config = read_json_file(job_config)
    else:
        config = read_job_config(workspace)

    if "id" not in config:
        raise ValueError("Must set id in config file.")
    return config["id"]


def init_job_use_workspace(data_client, namespace, workspace):
    """Use workspace to init job."""
    job_config = read_job_config(workspace)

    remote_root_path = __generate_remote_root_path(job_config)
    __fill_job_config(workspace, job_config, remote_root_path)
    __upload_workspace(data_client, namespace, workspace, remote_root_path)
    return job_config


def __generate_remote_root_path(job_config):
    if "id" not in job_config:
        raise ValueError("id must set in config.json")
    return "fl-" + job_config["id"]


def read_job_config(workspace):
    """Read job config."""
    job_config_file = os.path.join(workspace, WORKSPACE_JOB_CONFIG)
    if not os.path.exists(job_config_file):
        raise ValueError("the job config config.json should be in %s" %
                         job_config_file)
    return read_json_file(job_config_file)


def __fill_job_config(workspace, job_config, remote_root_path):
    __fill_model_path(workspace, job_config, remote_root_path)
    __fill_scripts(workspace, job_config, remote_root_path)
    __fill_extender(workspace, job_config, remote_root_path)


def __fill_model_path(workspace, job_config, remote_root_path):
    if __not_use_model_path(job_config):
        return

    local_model_path = os.path.join(workspace, WORKSPACE_MODEL)
    if not os.path.exists(local_model_path):
        raise FileNotFoundError("directory model should be in workspace, "
                                "and in model should have init model to "
                                "run federate learning")

    file_name = __find_model_path(local_model_path)
    if not file_name:
        raise FileNotFoundError("there should be have *.pth (pytorch) or *.h5"
                                " (tensorflow) file saved init model in "
                                "model directory")
    job_config["model_path"] = os.path.join(remote_root_path,
                                            WORKSPACE_MODEL, file_name)


def __find_model_path(local_model_path):
    for file_name in os.listdir(local_model_path):
        if file_name.endswith(".pth") or file_name.endswith(".h5"):
            return file_name
    return None


def __fill_scripts(workspace, job_config, remote_root_path):
    scripts_path = os.path.join(workspace, WORKSPACE_SCRIPTS)
    if os.path.exists(scripts_path):
        job_config["scripts"]["path"] = os.path.join(remote_root_path,
                                                     WORKSPACE_SCRIPTS)


def __fill_extender(workspace, job_config, remote_root_path):
    scripts_path = os.path.join(workspace, WORKSPACE_EXTENDER)
    if os.path.exists(scripts_path):
        if "extender" not in job_config:
            logging.warning("extender in job config is not set, but exist "
                            "in workspace, this would be wrong.")
            job_config["extender"] = {}
        job_config["extender"]["script_path"] = os.path.join(
            remote_root_path, WORKSPACE_EXTENDER)


def __upload_workspace(data_client, namespace, workspace, remote_root_path):
    click.echo("start upload %s to %s" % (workspace, remote_root_path))
    data_client.upload_files(namespace, workspace, remote_root_path)
    click.echo("upload success.")


def __not_use_model_path(job_config):
    return (job_config.get("model_id", None)
            or job_config.get("checkpoint_id", None))
