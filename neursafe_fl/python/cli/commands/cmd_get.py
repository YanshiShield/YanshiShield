#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=broad-except, too-many-arguments
"""subcommmand of get job.
"""
from io import BytesIO
import json
import os
import sys

from absl import logging
import click

from neursafe_fl.python.cli.core.context import PASS_CONTEXT, LOG_FILE
from neursafe_fl.python.cli.core.data_client import DataClient
from neursafe_fl.python.cli.core.job import Job
from neursafe_fl.python.cli.core.util import parse_job_id
from neursafe_fl.python.cli.core.model import Model

METRICS_FILE = "metrics.json"


@click.group("get", short_help="Get federated jobs, models or"
                               " federated server config info.")
def cli():
    """
     Get federated job, model, config details info. \n
     Run 'nsfl-ctl get COMMAND --help' for more information on sub-commands.
    """


@cli.command("jobs", short_help="Get jobs info.")
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
@click.option("-o", "--output", default=None,
              type=click.Choice(['yaml', 'json'], case_sensitive=False),
              help="Show all items in yaml or json format.")
@PASS_CONTEXT
def get_jobs(ctx, namespace, output, job_id=None, job_config=None,
             workspace=None):
    """(Noting: This command is same as 'get job')

    \b
    Get info of the federated jobs, you can get brief information of
     the jobs under one namespace in the form of a table.
    For example: \n
        nsfl-ctl get jobs default

    You can also get the details information of a given job, which you can
     specify by its job_id, or the config file when created the job.
    For example: \n
        nsfl-ctl get jobs default job_1 \n

        nsfl-ctl get jobs default -f /path/to/job_config.json  \n

        nsfl-ctl get jobs default -w /path/to/workspace \n

    """
    try:
        _id = parse_job_id(job_id, job_config, workspace)
        if _id:
            __show_job(ctx, namespace, _id, output)
        else:
            __show_jobs(ctx, namespace)
    except Exception as err:
        logging.exception(str(err))
        click.echo("Error message: %s, the detail see %s" % (
            str(err), LOG_FILE))
        sys.exit(1)


@cli.command("job", short_help="Get jobs info, same as 'get jobs'.")
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
@click.option("-o", "--output", default=None,
              type=click.Choice(['yaml', 'json'], case_sensitive=False),
              help="Show all item in yaml or json format.")
@PASS_CONTEXT
def get_job(ctx, namespace, output, job_id=None, job_config=None,
            workspace=None):
    """(Noting: This command is same as 'get jobs')

    Get info of the federated jobs, you can get brief information of all jobs
    under one namespace in the form of a table. For example: \n
        nsfl-ctl get job default

    You can also get the details information of a given job, which you can
     specify by its job_id, or the config file when created the job.
    For example: \n
        nsfl-ctl get job default job_1 \n
        nsfl-ctl get job default -f /path/to/job_config.json  \n
        nsfl-ctl get job default -w /path/to/workspace \n
    """
    try:
        _id = parse_job_id(job_id, job_config, workspace)
        if _id:
            __show_job(ctx, namespace, _id, output)
        else:
            __show_jobs(ctx, namespace)
    except Exception as err:
        logging.exception(str(err))
        click.echo("Error message: %s, the detail see %s" % (
            str(err), LOG_FILE))
        sys.exit(1)


@cli.command("namespace", short_help="Get user's namespaces.")
@PASS_CONTEXT
def get_namespace(ctx):
    """List namespaces that user has the permissions.
    """
    try:
        data_client = DataClient(ctx.get_data_server(), ctx.get_user(),
                                 ctx.get_password())

        namespaces = []
        for i in data_client.list('', '/'):
            if i["type"] == "directory":
                namespaces.append(i["display_name"])

        click.echo("user support namespaces: %s" % namespaces)
    except Exception as err:
        logging.exception(str(err))

        click.echo("Error message: %s, the detail see %s" % (
            str(err), LOG_FILE))
        sys.exit(1)


@cli.command("config", short_help="Get federated server config.")
@PASS_CONTEXT
def get_config(ctx):
    """Get the configuration of the remote federated server.
    """
    try:
        cmd_config = ctx.get_config()
        keys = ["api_server", "data_server", "certificate", "user", "password"]
        for key in keys:
            if key in cmd_config:
                click.echo("%s: %s" % (key, cmd_config[key]))
            else:
                click.echo("%s: none" % key)
    except Exception as err:
        logging.exception(str(err))
        click.echo("Error message: %s, the detail see %s" % (
            str(err), LOG_FILE))
        sys.exit(1)


def __show_jobs(ctx, namespace):
    fl_job = Job(ctx.get_api_server())
    job_configs = fl_job.get_jobs(namespace)
    __pretty_show_jobs(job_configs["jobs"])


def __show_job(ctx, namespace, job_id, output):
    fl_job = Job(ctx.get_api_server())
    job_config = fl_job.get_job(namespace, job_id)
    if output:
        metrics = __get_last_metrics(ctx, namespace, job_id, job_config)
        __pretty_show_job(job_config, output, metrics)
    else:
        __pretty_show_jobs([job_config])


def __pretty_show_job(job_config, output, metrics):
    job_config["metrics"] = metrics

    if output == "yaml":
        keys = ["id", "namespace", "description", "model_id", "model_path",
                "runtime", "resource", "task_entry", "scripts", "clients",
                "selector_address", "ssl", "port", "datasets", "parameters",
                "hyper_parameters", "secure_algorithm", "extenders", "output",
                "create_time", "start_time", "status", "metrics",
                "checkpoints"]

        for key in keys:
            if job_config.get(key, None):
                if isinstance(job_config.get(key), dict):
                    __show_dict(key, job_config.get(key), 4)
                else:
                    click.echo("%s: %s" % (key, job_config.get(key)))
    else:
        obj_json = json.dumps(job_config, indent=4)
        click.echo(obj_json)


def __show_dict(key, value, space_num):
    click.echo(" " * (space_num - 4) + key + ":")

    for sub_key, sub_value in value.items():
        if isinstance(sub_value, dict):
            __show_dict(sub_key, sub_value, space_num + 4)
        else:
            show_format = "{0: <%s}{1}: {2}" % space_num
            click.echo(show_format.format(" ", sub_key, sub_value))


def __pretty_show_jobs(job_configs):
    """Show job configs."""
    if job_configs:
        show_interval, new_configs = __get_show_info(job_configs)
        show_format = "{0: <%s}{1: <12}{2: <12}{3: <15}" % show_interval
        click.echo(show_format.format("id", "status",
                                      "progress", "create time"))
        for item in new_configs:
            click.echo(
                show_format.format(
                    item["id"], item["status"],
                    item["progress"], item["create_time"]))


def __get_show_info(job_configs):
    """get show information."""
    output_list = []
    max_len = 0
    for job_config in job_configs:
        _id = job_config["id"]
        output_list.append({"id": _id,
                            "status": job_config["status"]["state"],
                            "progress": job_config["status"]["progress"],
                            "create_time": job_config["create_time"]})
        max_len = max(max_len, len(_id))
    if max_len <= 4:
        show_interval = 7
    else:
        show_interval = max_len + 3
    return show_interval, output_list


def __get_last_metrics(ctx, namespace, job_id, job_config):
    if not (job_config.get("output", None)
            and job_config["status"]["state"] == "FINISHED"):
        return None

    data_client = DataClient(ctx.get_data_server(), ctx.get_user(),
                             ctx.get_password())

    paths = data_client.list(namespace, job_config.get("output"))
    pattern = "fl_%s_output_V" % job_id

    def get_serial_number(path_name):
        if pattern in path_name:
            return int(path_name[len(pattern):])

        return 0

    def get_metrics(output):
        metrics_file_path = os.path.join(output, METRICS_FILE)

        if data_client.exists(namespace, metrics_file_path):
            file_obj = BytesIO()
            data_client.download_fileobj(namespace, metrics_file_path, file_obj)
            file_obj.seek(0)

            return json.load(file_obj)

        return None

    def extract_metrics():
        for key, value in metrics.items():
            if isinstance(value, list):
                metrics[key] = value[-1]
        return metrics

    paths.sort(key=lambda info: get_serial_number(info["display_name"]),
               reverse=True)

    for path_ in paths:
        if path_["type"] == "directory" and pattern in path_["display_name"]:
            metrics = get_metrics(path_["name"].lstrip(namespace))

            if metrics:
                return extract_metrics()

    return None


@cli.command("models", short_help="Get models info.")
@click.argument("namespace")
@click.argument("name", required=False, default=None)
@click.argument("version", required=False, default=None)
@click.option("-id", "--model-id", default=None, required=False,
              help="The unique id of the model, you can get model's id"
                   " through get command.")
@click.option("-o", "--output", default=None,
              type=click.Choice(['yaml', 'json'], case_sensitive=False),
              help="Show all items in yaml or json format.")
@PASS_CONTEXT
def get_models(ctx, namespace, output, name=None, version=None,
               model_id=None):
    """(Noting: This command is same as 'get model')

    Get the models info in the model store.

    For examples: \n
    Get all the models in one namespace. \n
        nsfl-ctl get models default

    Get brief information of all the versions of one model. \n
        nsfl-ctl get models default mnist

    Get the details of specified version of one model. \n
        nsfl-ctl get models default mnist V1

        nsfl-ctl get models -id model_1

        nsfl-ctl get models -id model_2 -o json
    """
    try:
        fl_model = Model(ctx.get_api_server())
        if model_id:
            model = fl_model.get_model_by_id(model_id)
            _show_model_detail(model, output)
        else:
            if not name:
                # get all the model in namespace
                models = fl_model.get_models(namespace)
                _show_models(namespace, models, output)
            else:
                models = fl_model.get_model(namespace, name, version)
                if not version:  # show all the version of model
                    _show_model_versions(namespace, name, models[name])
                else:
                    _show_model_detail(models[name], output)

    except Exception as err:
        logging.exception(str(err))
        click.echo("Error message: %s, the detail see %s" % (
            str(err), LOG_FILE))
        sys.exit(1)


def _show_models(namespace, models, output):
    """Show all the model in the namespace.
    """
    del output
    click.echo("--------------------------Model List--------------------------")
    click.echo("Namespace: %s  " % namespace)
    click.echo("--------------------------------------------------------------")
    if models:
        show_format = "{0: <12}{1: <15}{2: <12}"
        click.echo(show_format.format("No.", "name", "versions_num"))
        serial = 1
        for name, model in models.items():
            click.echo(show_format.format(serial, name, len(model)))
            serial += 1
    else:
        click.echo("No models")


def _show_model_versions(namespace, name, model_versions):
    click.echo("--------------------------Model Info--------------------------")
    click.echo("namespace: %s    name: %s " % (namespace, name))
    click.echo("---------------------------Versions---------------------------")
    if model_versions:
        show_interval, simplified_info = __simplify_model_info(model_versions)
        show_format = "{0: <%s}{1: <12}{2: <12}{3: <12}{4: <15}" % show_interval
        click.echo(show_format.format("id", "version", "runtime",
                                      "state", "create_time"))
        for item in simplified_info:
            click.echo(show_format.format(item["id"], item["version"],
                                          item["runtime"], item["state"],
                                          item["create_time"]))
    else:
        click.echo("No versions of model")


def __simplify_model_info(models_info):
    output_list = []
    max_len = 0
    for model_info in models_info:
        _id = model_info["id"]
        output_list.append({"id": _id,
                            "runtime": model_info["runtime"],
                            "version": model_info["version_info"]["version"],
                            "state": model_info["state"],
                            "create_time": model_info["version_info"]["time"]})
        max_len = max(max_len, len(_id))
    if max_len <= 4:
        show_interval = 7
    else:
        show_interval = max_len + 3
    return show_interval, output_list


def _show_model_detail(model_info, output):
    """Show the model with detail information.
    """
    if not model_info:
        click.echo("Not found.")
        return

    if isinstance(model_info, list):
        model_info = model_info[0]

    show_keys = ["namespace", "name", "runtime", "id", "state", "version_info",
                 "model_path", "error_msg"]

    if output == "yaml":
        for key in show_keys:
            if model_info.get(key, None):
                if isinstance(model_info.get(key), dict):
                    __show_dict(key, model_info.get(key), 4)
                else:
                    click.echo("%s: %s" % (key, model_info.get(key)))
    else:
        for key in list(model_info.keys()):
            if key not in show_keys:
                del model_info[key]

        obj_json = json.dumps(model_info, indent=4)
        click.echo(obj_json)


@cli.command("model", short_help="Get models info, same as 'get models'.")
@click.argument("namespace")
@click.argument("name", required=False, default=None)
@click.argument("version", required=False, default=None)
@click.option("-id", "--model-id", default=None, required=False,
              help="The unique id of the model, you can get model's id"
                   " through get command.")
@click.option("-o", "--output", default=None,
              type=click.Choice(['yaml', 'json'], case_sensitive=False),
              help="Show all items in yaml or json format.")
@PASS_CONTEXT
def get_model(ctx, namespace, output, name=None, version=None,
              model_id=None):
    """(Noting: This command is same as 'get models')

    Get the models info in the model store.

    For examples: \n
    Get all the models in one namespace. \n
        nsfl-ctl get model default

    Get brief information of all the versions of one model. \n
        nsfl-ctl get model default mnist

    Get the details of specified version of one model. \n
        nsfl-ctl get model default mnist V1

        nsfl-ctl get model -id model_1

        nsfl-ctl get model -id model_2 -o json
    """
    try:
        fl_model = Model(ctx.get_api_server())
        if model_id:
            model = fl_model.get_model_by_id(model_id)
            _show_model_detail(model, output)
        else:
            if not name:
                # get all the model in namespace
                models = fl_model.get_models(namespace)
                _show_models(namespace, models, output)
            else:
                models = fl_model.get_model(namespace, name, version)
                if not version:  # show all the version of model
                    _show_model_versions(namespace, name, models[name])
                else:
                    _show_model_detail(models[name], output)

    except Exception as err:
        logging.exception(str(err))
        click.echo("Error message: %s, the detail see %s" % (
            str(err), LOG_FILE))
        sys.exit(1)
