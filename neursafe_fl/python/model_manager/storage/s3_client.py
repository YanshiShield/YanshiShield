#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=broad-except, no-member
"""S3 interface for object storage.
"""
import boto3
from neursafe_fl.python.model_manager.storage.base_io import StorageInterface,\
    PathNotExist, StorageError


class S3Client(StorageInterface):
    """Amazon S3 storage interface implementation.
    """

    def __init__(self, **kwargs):
        self.__client = boto3.resource(
            's3',
            aws_access_key_id=kwargs.get("access_key"),
            aws_secret_access_key=kwargs.get("secret_key"),
            endpoint_url=kwargs.get("endpoint")
        )

    def copy(self, src, target, callback=None):
        """Copy object from one bucket to another bucket.
        """
        if not self.exist(src):
            raise PathNotExist("Src %s not exist." % src)
        copy_source = {
            "Bucket": src["namespace"],
            "Key": src["path"]
        }
        self.__client.meta.client.copy(copy_source,
                                       target["namespace"], target["path"])

    def delete(self, target, callback=None):
        """Delete object in bucket.
        """
        if not self.exist(target):
            raise PathNotExist("Target %s not exist." % target)
        self.__client.Object(target["namespace"], target["path"]).delete()

    def exist(self, target):
        """Check if the object exist.
        """
        try:
            response = self.__client.meta.client.head_object(
                Bucket=target["namespace"],
                Key=target["path"],
            )
            if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                return True

        except Exception as err:
            if hasattr(err, "response"):
                err_code = err.response["Error"]["Code"]
                if err_code == 404:
                    return False
            else:
                raise StorageError(str(err)) from err
        return False
