# -*- coding: utf-8 -*-
"""
Mount S3 bucket via FUSE, convert s3 object to the native object
format for files
"""

import os
import time
from absl import logging

import boto3
import botocore


MAX_RETRY_TIMES = int(os.getenv("MAX_RETRY_TIMES", "2"))
RETRY_INTERNAL = int(os.getenv("RETRY_INTERNAL", "1"))
WAIT_MOUNT_TIMEOUT = int(os.getenv("WAIT_MOUNT_TIMEOUT", "300"))


class MountBucketError(Exception):
    """Mount S3 bucket error"""


def convert_s3_to_posix(bucket_name, endpoint_url,  # noqa: C901
                        access_key, secret_key,
                        mount_path):
    """
    Mount s3 bucket to local path(s3fs-fuse has already installed).

    Args:
        bucket_name: s3 bucket name.
        endpoint_url: storage service access url.
        access_key: storage service access key.
        secret_key: storage service secret key.
        mount_path: local mount path
    """
    passwd_file = "/.passwd-s3fs"

    def check_bucket_valid():
        retry_num = 0

        while retry_num <= MAX_RETRY_TIMES:
            try:
                s3_client = boto3.resource(
                    's3',
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    endpoint_url=endpoint_url
                )

                if s3_client.Bucket(bucket_name) not in s3_client.buckets.all():
                    raise MountBucketError("Bucket:%s not exist." % bucket_name)

                logging.info("Check bucket successfully.")
                return
            except botocore.exceptions.EndpointConnectionError as error:
                logging.warning(str(error))
                retry_num += 1
                time.sleep(RETRY_INTERNAL)
            except botocore.exceptions.ClientError as error:
                raise MountBucketError(str(error)) from error

        raise MountBucketError("Can not connect to %s." % endpoint_url)

    def gen_passwd_file():
        with open(passwd_file, "w") as file:
            file.write("%s:%s" % (access_key, secret_key))

        os.chmod(passwd_file, 640)

    def check_mount_path_valid():
        if not os.path.exists(mount_path):
            os.makedirs(mount_path)

        if os.listdir(mount_path):
            raise MountBucketError("%s not empty." % mount_path)

    def mount_bucket():
        shell_cmd = "s3fs %s %s -o no_check_certificate " \
                    "-o passwd_file=%s " \
                    "-o use_path_request_style " \
                    "-o url=%s " \
                    "-o allow_other" % (bucket_name, mount_path,
                                        passwd_file, endpoint_url)

        status = os.system(shell_cmd)

        if status:
            raise MountBucketError("Execute command failed: %s" % shell_cmd)

    def wait_mount_successfully():
        retry_times = 0

        while retry_times <= WAIT_MOUNT_TIMEOUT:
            if os.path.ismount(mount_path):
                logging.info("Path: %s already mounted." % mount_path)
                return

            logging.info("Path: %s is mounting." % mount_path)
            retry_times += 1
            time.sleep(RETRY_INTERNAL)

        raise MountBucketError("Wait mounting successfully time out.")

    def clear():
        if os.path.exists(passwd_file):
            os.remove(passwd_file)

    if os.path.ismount(mount_path):
        logging.warning("Path: %s is mounted." % mount_path)
        return

    check_bucket_valid()
    check_mount_path_valid()
    gen_passwd_file()
    mount_bucket()
    wait_mount_successfully()
    clear()
