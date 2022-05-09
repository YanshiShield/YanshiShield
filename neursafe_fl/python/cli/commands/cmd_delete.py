#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=broad-except
"""subcommmand of delete job.
"""
import sys

from absl import logging
import click

from neursafe_fl.python.cli.core.util import parse_job_id
from neursafe_fl.python.cli.core.context import PASS_CONTEXT, LOG_FILE
from neursafe_fl.python.cli.core.job import Job
from neursafe_fl.python.cli.core.model import Model


@click.group("delete", short_help="Used to delete job or model.")
def cli():
    """Delete job or model command."""


@cli.command("job", short_help="Delete job.")
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
def delete_job(ctx, namespace, job_id=None, job_config=None,
               workspace=None):
    """Delete job.
    """
    try:
        _id = parse_job_id(job_id, job_config, workspace)
        if not _id:
            raise ValueError("Must set job_id.")

        fl_job = Job(ctx.get_api_server())
        fl_job.delete(namespace, _id)
        click.echo("Delete job %s success, you can use "
                   "'nsfl get job' to query job status." % _id)
    except Exception as err:
        logging.exception(str(err))
        click.echo("Error message: %s, the detail see %s" % (
            str(err), LOG_FILE))
        sys.exit(1)


@cli.command("model", short_help="Delete model.")
@click.argument("namespace", required=False)
@click.argument("name", required=False, default=None)
@click.argument("version", required=False, default=None)
@click.option("-id", "--model_id", default=None, required=False,
              help="The unique id of this model.")
@PASS_CONTEXT
def delete_model(ctx, namespace=None, name=None, version=None,
                 model_id=None):
    """Delete model.

    \b
    Delete one model in the namespace. You can delete model by two ways.
        1. fill in the namespace, model and version. then will delete this
          model. if version is ignored, then all the version of this model
          will be deleted.
        2. fill in the model_id through the -id option. and will only delete
          this unique model.
    """
    try:
        fl_model = Model(ctx.get_api_server())
        if model_id:
            fl_model.delete_model_by_id(model_id)
        else:
            if not namespace or not name:
                raise Exception("Must specify model namespace and name when "
                                "delete model.")
            fl_model.delete(namespace, name, version)

        click.echo("delete model success")

    except Exception as err:
        logging.exception(str(err))
        click.echo("Error message: %s, the detail see %s" % (
            str(err), LOG_FILE))
        sys.exit(1)
