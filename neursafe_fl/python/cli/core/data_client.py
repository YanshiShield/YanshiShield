#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Data client.
"""

import os
import math

import boto3
from boto3.s3.transfer import TransferConfig
from neursafe_fl.python.cli.core.aes import decrypt
from neursafe_fl.python.cli.core.progress import ProgressPercentage
from neursafe_fl.python.cli.core.util import get_size

GB = 1024 ** 3
MAX_UPLOAD_SIZE = 5 * GB


class DataClient:
    """The data client to operate data"""
    def __init__(self, data_server, user, password, cert_path):
        if cert_path:
            self.__client = boto3.client(
                's3',
                aws_access_key_id=user,
                aws_secret_access_key=decrypt(password),
                endpoint_url=data_server,
                use_ssl=True,
                verify=cert_path
            )
        else:
            self.__client = boto3.client(
                's3',
                aws_access_key_id=user,
                aws_secret_access_key=decrypt(password),
                endpoint_url=data_server
            )

        self.__trans_conf = TransferConfig(multipart_threshold=MAX_UPLOAD_SIZE)
        self.__total_size = 0
        self.__uploaded_size = 0
        self.progress = 0

    def upload_file(self, namespace, local_file, remote_file):
        """Upload a file to server.

        Args:
            namespace: job's namespace.
            local_file: a Local absolute path.
            remote_file: the file path in server.
        """
        if remote_file.startswith("/"):
            remote_file = remote_file[1:]
        self.__total_size = get_size(local_file)

        self.__client.upload_file(local_file, namespace, remote_file,
                                  Callback=ProgressPercentage(
                                      local_file, self.__total_progress),
                                  Config=self.__trans_conf)

    def upload_files(self, namespace, local_dir, remote_dir):
        """Upload all files in path to server.

        Args:
            namespace: job's namespace.
            local_dir: a Local absolute path.
            remote_dir: the file path in server.
        """
        if remote_dir.startswith("/"):
            remote_dir = remote_dir[1:]
        self.__total_size = get_size(local_dir)

        self.__upload_files(namespace, local_dir, remote_dir)

    def __upload_files(self, namespace, local_dir, remote_dir):
        for path in os.listdir(local_dir):
            src = os.path.join(local_dir, path)
            dest = os.path.join(remote_dir, path)
            if os.path.isfile(src):
                self.__client.upload_file(src, namespace, dest,
                                          Callback=ProgressPercentage(
                                              src, self.__total_progress),
                                          Config=self.__trans_conf)
                print("")
            elif os.path.isdir(src):
                self.__upload_files(namespace, src, dest)

    def __total_progress(self, byte_amount):
        self.__uploaded_size += byte_amount
        self.progress = math.floor((
            self.__uploaded_size / float(self.__total_size)) * 100)

    def download_file(self, namespace, remote_file, _file):
        """Download remote file to local.

        Args:
            namespace: job's namespace.
            remote_file: the file path in server.
            _file: a Local absolute path or a flie-like obj.
        """
        if remote_file.startswith("/"):
            remote_file = remote_file[1:]

        file_size = self.__client.head_object(
            Bucket=namespace, Key=remote_file).get("ContentLength", 1)

        progress = ProgressPercentage(remote_file, download=True,
                                      size=file_size)
        if isinstance(_file, str):
            self.__client.download_file(namespace, remote_file, _file,
                                        Callback=progress,
                                        Config=self.__trans_conf)
        else:
            self.__client.download_fileobj(namespace, remote_file, _file,
                                           Config=self.__trans_conf)

    def download_files(self, namespace, remote_dir, local_dir):
        """Download all files in server to local.

        Args:
            namespace: job's namespace.
            remote_dir: the file path in server.
            local_dir: a Local absolute path.
        """
        if remote_dir.startswith("/"):
            remote_dir = remote_dir[1:]

        objs = self.__client.list_objects(Bucket=namespace, Prefix=remote_dir)
        for obj in objs["Contents"]:
            # print(obj.object_name, obj.is_dir)
            dest = os.path.join(local_dir, obj["Key"])
            if not os.path.exists(os.path.dirname(dest)):
                os.makedirs(os.path.dirname(dest))

            self.__client.download_file(namespace, obj["Key"], dest,
                                        Config=self.__trans_conf)

    def list_namespaces(self):
        """List namespaces"""
        buckets = self.__client.list_buckets()
        namespaces = []
        for bucket in buckets['Buckets']:
            namespaces.append(bucket["Name"])
        return namespaces

    def list_objects(self, namespace, remote_dir):
        """List objects"""
        if remote_dir.startswith("/"):
            remote_dir = remote_dir[1:]

        return self.__client.list_objects(Bucket=namespace, Prefix=remote_dir)
