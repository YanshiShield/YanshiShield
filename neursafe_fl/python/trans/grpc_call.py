#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-many-arguments
"""Process transfer in GRPC.
"""
from io import BytesIO
import os

from absl import logging

from neursafe_fl.proto.message_pb2 import FilePackage, File
from neursafe_fl.python.trans.grpc_pool import GRPCPool


class RemoteServerError(Exception):
    """When GRPC server process error, raise this error.
    """


async def stream_call(stub_class, call_method, message_type, address,
                      config=None, file_paths=None, file_like_objs=None,
                      certificate_path=None, metadata=None):
    """Used server call client or client report result to server.

    Args:
        stub_class: TrainServiceStub, etc. defined in proto message.
        call_method: the method defined in stub_class to call.
        message_type: Task or TaskResult, defined in proto message.
        address: The destination server, like host:port.
        config: a object of message_type,
        file_paths: [string, ], element in list is an exist file's path.
        file_like_objs: [(file_info, file_like_obj), ],
            file_info: the object of File, defined in proto message.
            file_like_obj:Lmaybe BytesIO, StringIO, etc.
        certificate_path: Used in grpcs, where the certificate.
        metadata: grpc metadata.
    """
    channel = GRPCPool.instance().get_channel(address, certificate_path)

    stub = stub_class(channel)
    method = getattr(stub, call_method)

    datas = __gen_data_sequence(message_type,
                                config, file_paths, file_like_objs)
    reply = await method(datas, metadata=metadata)
    __assert_reply(address, reply)


def __gen_data_sequence(message_type,
                        config, file_paths, file_like_objs):
    data_sequence = []
    if config:
        data_sequence.append(config)

    if file_paths:
        for file_path in file_paths:
            __add_file(data_sequence, message_type, file_path)

    if file_like_objs:
        for file_info, file_like_obj in file_like_objs:
            __add_file_like_obj(
                data_sequence, message_type, file_info, file_like_obj)
    return data_sequence


def __assert_reply(address, reply):
    logging.info('From %s reply: %s', address, reply)
    if reply.state == 'failed':
        raise RemoteServerError(
            'Received from %s error: %s' % (address, reply.reason))


def __add_file(data_sequence, message_type, file_path):
    with open(file_path, 'rb') as file_io:
        data_sequence.append(message_type(
            files=FilePackage(
                file_info=_gen_file_info(file_path))))

        file_io.seek(0)
        chunk = file_io.read()
        data_sequence.append(message_type(
            files=FilePackage(
                chunk=chunk)))


def __add_file_like_obj(data_sequence, message_type,
                        file_info, file_like_obj):
    data_sequence.append(message_type(
        files=FilePackage(
            file_info=file_info)))

    file_like_obj.seek(0)
    chunk = file_like_obj.read()
    data_sequence.append(
        message_type(
            files=FilePackage(
                chunk=chunk)))


def _gen_file_info(data):
    filename = os.path.basename(data)
    compress = filename.endswith('.zip')
    return File(
        name=filename,
        compress=compress)


def extract_metadata(stream, keys=None):
    """Extract metadata from grpc request."""
    metadata = {}
    if stream.metadata:
        for meta_key in stream.metadata:
            if not keys or meta_key in keys:
                metadata[meta_key] = stream.metadata[meta_key]
    return metadata


async def unpackage_stream(stream, validate_func=None):
    """
    Unpackage data from GRPC server.

    Args:
        stream: The grpc stream, where to unpackage.
        validate_func: Maybe need validate the data from stream.

    Return:
        return a dict which contain the data unpackaged from stream.
        like: (Task or TaskResult,
               [('file_info': File, defined in proto message
                 'object': the object of BytesIO
               ),]
              )
    """
    config = None
    files = []
    async for data in stream:
        if data.HasField('metadata'):
            config = data
            if validate_func:
                validate_func(config)
        elif data.HasField('files'):
            if data.files.file_info.name != '':
                memory_writer = BytesIO()

                files.append((
                    data.files.file_info,
                    memory_writer
                ))
            else:
                memory_writer.write(data.files.chunk)

    return config, files


async def unary_call(stub_class, call_method, data, address,
                     certificate_path, metadata=None):
    """Call without stream.
    """
    channel = GRPCPool.instance().get_channel(address, certificate_path)
    stub = stub_class(channel)
    method = getattr(stub, call_method)
    return await method(data, metadata=metadata)
