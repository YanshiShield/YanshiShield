#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=no-member

"""
Report delta weights, metrics and other info to server.
"""
import os
import pickle

from io import BytesIO
from absl import logging

import neursafe_fl.python.sdk.utils as utils
from neursafe_fl.proto.message_pb2 import TaskResult, Status, File
from neursafe_fl.python.client.workspace.custom import read_result_parameters, \
    get_result_path
from neursafe_fl.python.utils.file_io import zip_files, list_all_files
from neursafe_fl.proto.reply_service_grpc import TrainReplyServiceStub, \
    EvaluateReplyServiceStub
from neursafe_fl.python.trans.grpc_call import stream_call


def _get_custom_parameters(workspace):
    return read_result_parameters(workspace)


def _list_custom_files(workspace):
    result_path = get_result_path(workspace)

    return list_all_files(result_path)


def _encode_task_result(status, task_metadata, client_id,
                        metrics=None, custom_params=None):
    task_result = TaskResult(metadata=task_metadata,
                             client_id=client_id,
                             status=status)

    if metrics:
        task_result.spec.metrics.update(metrics)

    if custom_params:
        task_result.spec.custom_params.update(custom_params)

    return task_result


def _zip_files(workspace, custom_files):
    if custom_files:
        result_path = get_result_path(workspace)

        files = []

        for filename in custom_files:
            files.append(('custom/' + filename,
                          os.path.join(result_path, filename)))

        file_info = File(name='result.zip',
                         compress=True)

        return file_info, zip_files(files)

    return None


def _submit_trained_result(metrics, weights):
    (task_metadata, grpc_metadata,
     server_address, ssl_certification_path, workspace) = _get_configuration()

    def prepare_task_result():
        custom_params = _get_custom_parameters(workspace)
        custom_files = _list_custom_files(workspace)

        task_result = _encode_task_result(Status.success, task_metadata,
                                          grpc_metadata["client_id"],
                                          metrics, custom_params)

        custom_files_io = _zip_files(workspace, custom_files)

        delta_weights_io = (File(name='delta_weights'),
                            BytesIO(pickle.dumps(weights)))

        return task_result, delta_weights_io, custom_files_io

    def do_submit():
        file_like_objs = [weights_io]

        if files_io:
            file_like_objs.append(files_io)

        utils.do_function_sync(stream_call, TrainReplyServiceStub, 'TrainReply',
                               TaskResult, server_address, config=result,
                               file_like_objs=file_like_objs,
                               certificate_path=ssl_certification_path,
                               metadata=grpc_metadata)

    result, weights_io, files_io = prepare_task_result()

    do_submit()


def _submit_evaluated_result(metrics):
    (task_metadata, grpc_metadata,
     server_address, ssl_certification_path, _) = _get_configuration()

    task_result = _encode_task_result(Status.success, task_metadata,
                                      grpc_metadata["client_id"],
                                      metrics=metrics)

    utils.do_function_sync(stream_call, EvaluateReplyServiceStub,
                           'EvaluateReply', TaskResult, server_address,
                           config=task_result,
                           certificate_path=ssl_certification_path,
                           metadata=grpc_metadata)


def _get_configuration():
    task_metadata = utils.get_task_metadata()
    grpc_metadata = utils.get_grpc_metadata()
    server_address = utils.get_server_address()
    ssl_certification_path = utils.get_ssl_certification_path()
    workspace = utils.get_task_workspace()

    return (task_metadata, grpc_metadata, server_address,
            ssl_certification_path, workspace)


def submit(metrics, weights=None):
    """Submit metrics or weights to coordinator

    Args:
        metrics: metrics of task
        weights: delta weights between trained weights and init weights.
    """
    if not weights and not metrics:
        logging.warning("Nothing needs to be submitted to server.")
        return

    if weights:
        # Training task needs to submit model weights to server.
        _submit_trained_result(metrics, weights)
    else:
        # Evaluation task dose not need to submit model weights to server.
        _submit_evaluated_result(metrics)
