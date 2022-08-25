#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Data client.
"""
import os

from webdav4.client import Client
from neursafe_fl.python.cli.core.progress import ProgressPercentage
from neursafe_fl.python.cli.core.aes import decrypt

TIMEOUT = 300
CHUNK_SIZE = 2**10


def _combine_path(prefix, relative_path):
    return os.path.join(prefix, relative_path.lstrip("/"))


class DataClient:
    """The data client to operate data"""
    def __init__(self, server_address, user, password):
        server = "http://%s" % server_address.lstrip("http://")
        self.__client = Client(server, auth=(user, decrypt(password)),
                               timeout=TIMEOUT)

    def __exists(self, remote_path):
        return self.__client.exists(remote_path)

    def __mkdirs(self, remote_dir_path):
        whole_dir = ""

        for child_dir in remote_dir_path.split('/'):
            whole_dir = os.path.join(whole_dir, child_dir)
            if not self.__client.exists(whole_dir):
                self.__client.mkdir(whole_dir)

    def upload_file(self, namespace, local_path, remote_path):
        """Upload a file to data server.

        Args:
            namespace: namespace which the file belongs to.
            local_path: local file absolute path.
            remote_path: remote file relative path in namespace.
        """
        remote_path = _combine_path(namespace, remote_path)

        remote_dir, _ = os.path.split(remote_path)

        if not self.__exists(remote_dir):
            self.__mkdirs(remote_dir)

        progress = ProgressPercentage(local_path)
        self.__client.upload_file(local_path, remote_path,
                                  overwrite=True,
                                  callback=progress,
                                  chunk_size=CHUNK_SIZE)

    def upload_files(self, namespace, local_dir, remote_dir):
        """Upload all files in director to data server.

        Args:
            namespace: namespace which the files belongs to.
            local_dir: local directory path.
            remote_dir: remote directory relative path in namespace.
        """
        for name_ in os.listdir(local_dir):
            src = os.path.join(local_dir, name_)
            dest = os.path.join(remote_dir, name_)
            if os.path.isfile(src):
                self.upload_file(namespace, src, dest)
                print("")
            elif os.path.isdir(src):
                self.upload_files(namespace, src, dest)

    def download_file(self, namespace, remote_path, local_path):
        """Download file to local path

        Args:
            namespace: namespace which the file belongs to.
            remote_path: remote file relative path in namespace.
            local_path: local file absolute path.
        """
        remote_path = _combine_path(namespace, remote_path)

        file_size = self.__client.info(remote_path)["content_length"]

        progress = ProgressPercentage(remote_path, download=True,
                                      size=file_size)

        self.__client.download_file(remote_path, local_path,
                                    callback=progress,
                                    chunk_size=CHUNK_SIZE)

    def download_fileobj(self, namespace, remote_path, file_obj):
        """Download file to file object.

        Args:
            namespace: namespace which the file belongs to.
            remote_path: remote file relative path in namespace.
            file_obj: file object.
        """
        remote_path = _combine_path(namespace, remote_path)

        self.__client.download_fileobj(remote_path, file_obj,
                                       chunk_size=CHUNK_SIZE)

    def download_files(self, namespace, remote_dir, local_dir):
        """
        Download all files in remote directory to local directory.

        Args:
            namespace: namespace which the files belongs to.
            remote_dir: remote directory relative path in namespace.
            local_dir: local directory path.
        """
        local_absolute_dir = _combine_path(local_dir, remote_dir)
        if not os.path.exists(local_absolute_dir):
            os.makedirs(local_absolute_dir)

        remote_absolute_dir = _combine_path(namespace, remote_dir)

        for info in self.__client.ls(remote_absolute_dir):
            relative_path = info["name"].lstrip(namespace)
            if info["type"] == "file":
                self.download_file(namespace, relative_path,
                                   _combine_path(local_dir, relative_path))
                print("")
            else:
                self.download_files(namespace, relative_path,
                                    local_dir)

    def list(self, namespace, remote_dir):
        """List remote directory

        Args:
            namespace: namespace which the directory belongs to.
            remote_dir: remote directory relative path in namespace.
        """
        remote_path = _combine_path(namespace, remote_dir)

        return self.__client.ls(remote_path)

    def exists(self, namespace, remote_path):
        """Check remote path exists.

        Args:
            namespace: namespace which the directory belongs to.
            remote_path: remote relative path in namespace.
        """
        remote_path = _combine_path(namespace, remote_path)

        return self.__client.exists(remote_path)
