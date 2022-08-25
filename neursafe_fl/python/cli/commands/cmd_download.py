#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-many-arguments, broad-except
"""sub command for download model.
"""
import os
import sys

from absl import logging
import click

from neursafe_fl.python.cli.core.context import PASS_CONTEXT, LOG_FILE
from neursafe_fl.python.cli.core.data_client import DataClient
from neursafe_fl.python.cli.core.model import Model


@click.group("download", short_help="Download model.")
def cli():
    """Download model to local filesystem.
    """


@cli.command("model", short_help="Download model.")
@click.argument("namespace", required=False, default=None)
@click.argument("name", required=False, default=None)
@click.argument("version", required=False, default=None)
@click.option("-id", "--model-id", default=None, required=False,
              help="The unique id of this model, you can get model's id"
                   " through get command.")
@click.option("-l", "--local-path", default=None, required=False,
              help="The local path to download the model, if not "
                   "specified, the model will be downloaded to current dir.")
@PASS_CONTEXT
def download_model(ctx, namespace=None, name=None, version=None,
                   model_id=None, local_path=None):
    """
    Download the model to local path. You can specify the model by its id,
     or by namespace/name/version.

    For example: \n
        nsfl-ctl download model -id model_1 -l /tmp  \n
        nsfl-ctl download model default mnist V1 -l /tmp \n
    """
    try:
        fl_model = Model(ctx.get_api_server())
        if model_id:
            model_info = fl_model.get_model_by_id(model_id)
        else:
            if not namespace or not name or not version:
                raise Exception("Must specify namespace, model_name, and "
                                "version when download model.")
            model_info = fl_model.get_model(namespace, name, version)[0]

        # download model
        click.echo("start download model")
        if not local_path:
            local_path = os.getcwd()

        if not os.path.exists(local_path):
            os.makedirs(local_path)

        data_client = DataClient(ctx.get_data_server(), ctx.get_user(),
                                 ctx.get_password())
        model_namespace = model_info["storage_info"][0]
        model_path = model_info["storage_info"][1]
        file_name = os.path.basename(model_path)
        data_client.download_file(model_namespace, model_path,
                                  os.path.join(local_path, file_name))

        click.echo("download success, path: %s" %
                   os.path.join(local_path, file_name))
    except Exception as err:
        logging.exception(str(err))
        click.echo("Error message: %s, the detail see %s" % (
            str(err), LOG_FILE))
        sys.exit(1)
