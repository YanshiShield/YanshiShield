#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Module encapsulate functions to call remote client's gRPC Service."""

from absl import logging

from neursafe_fl.proto.evaluate_service_grpc import EvaluateServiceStub
from neursafe_fl.proto.message_pb2 import Task
from neursafe_fl.proto.train_service_grpc import TrainServiceStub
from neursafe_fl.python.coordinator.errors import RemoteCallFailedError
from neursafe_fl.python.trans.grpc_call import stream_call, unary_call


async def train(client, job_id, task, file, ssl=None):
    """Client gRPC Service: Train function.

    Call the the remote train function provided by the device.

    Args:
        client: the service address provided by device
        job_id: the id of job
        task: task which will broadcat to client
        file: file which will broadcat to client
        ssl: grpcs's ssl.
    Raises:
        RemoteCallFailedError, when call function failed.
    """
    grpc_metadata = {"module-id": str(job_id),
                     "client_id": client}

    try:
        await stream_call(TrainServiceStub, "Train", Task, client, config=task,
                          file_like_objs=[file],
                          certificate_path=ssl, metadata=grpc_metadata)
    except Exception as err:
        logging.exception(str(err))
        raise RemoteCallFailedError("Remote client %s Train Service error, %s" %
                                    (client, str(err))) from err


async def evaluate(client, job_id, task, file, ssl=None):
    """Client Grpc Service: Evaluate function
    """
    grpc_metadata = {"module-id": str(job_id),
                     "client_id": client}

    try:
        await stream_call(EvaluateServiceStub, "Evaluate", Task, client,
                          config=task, file_like_objs=[file],
                          certificate_path=ssl, metadata=grpc_metadata)
    except Exception as err:
        logging.exception(str(err))
        raise RemoteCallFailedError("Remote client %s Evaluate Service error, "
                                    "%s" % (client, str(err))) from err


async def stop(client, metadata, task_type, ssl=None):
    """Client Grpc Service: Stop function
    """
    if task_type == "train":
        stub = TrainServiceStub
    elif task_type == "evaluate":
        stub = EvaluateServiceStub
    else:
        return

    try:
        await unary_call(stub, "Stop", metadata, client, certificate_path=ssl)
    except Exception as err:
        raise RemoteCallFailedError("Remote client %s stop error, "
                                    "%s" % (client, str(err))) from err
