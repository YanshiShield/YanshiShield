#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Client app, the entry of client.
"""

import asyncio

from absl import app
from absl import flags

from neursafe_fl.python.client.client import Client
from neursafe_fl.python.client.validation import validate_agent_config, \
    SUPPORT_PLATFORM
from neursafe_fl.python.utils.file_io import read_json_file
from neursafe_fl.python.utils.log import set_log
from neursafe_fl.python.utils.s3_conversion import convert_s3_to_posix
import neursafe_fl.python.client.const as const


DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 22000

flags.DEFINE_string('host', DEFAULT_HOST,
                    'The host the client listens on, which is an IP address..')
flags.DEFINE_integer('port', DEFAULT_PORT,
                     'The port the client is listening on.')
flags.DEFINE_string('server', None,
                    'The address of the server, where the training and '
                    'evaluation results are reported, the format is ip:port.')
flags.DEFINE_string('workspace', None,
                    "Client's workspace path. The working path of the task "
                    'will save the temporary files generated during training'
                    ' or evaluation, such as initial weights, weights after '
                    'training, etc.')
flags.DEFINE_string('platform', "linux",
                    'The running platform of the client, support %s.'
                    % SUPPORT_PLATFORM)
flags.DEFINE_string('task_config_entry', None,
                    'The path where the entry file of the task is stored. The '
                    'entry files are some *.json files. These files describe '
                    'the working path and startup command of the task.')
flags.DEFINE_integer('storage_quota', 10240,
                     'The storage quota (MB) of the workspace for storing '
                     'temporary files. This is to ensure that the storage of '
                     'the workspace does not exceed the quota. When the quota'
                     ' is exceeded, the client will clean up the workspace.')
flags.DEFINE_string('log_level', 'INFO',
                    'Log level, support [DEBUG, INFO, WARNING, ERROR].')
flags.DEFINE_string('ssl', None,
                    'If grpcs is used, ssl must be set, else not. It sets a '
                    'path and three files under the path:\n'
                    "cert.pem: This file saves client's certificate\n"
                    "private.key: This file saves client's private key\n"
                    'trusted.pem: This file saves the trusted certificate, '
                    '   which needs to include the certificate of the '
                    '   coordinator or proxy')
flags.DEFINE_string('datasets', None,
                    'A json formatted file that saves the configuration of '
                    'the dataset. The file saves the key-value pair of the '
                    'dataset name and the path where the dataset is located.')
flags.DEFINE_string('config_file', None,
                    'The configuration file in json format started by the '
                    'client. In this configuration file, you can configure '
                    'key-value pairs for other parameters. If this '
                    'configuration file is used, the client will preferentially'
                    ' use the parameters in the configuration file.')

FLAGS = flags.FLAGS


def __parse_config_file(file_name):
    return read_json_file(file_name)


def __set_default_value(config):
    config['log_level'] = config.get('log_level', FLAGS.log_level)
    config['host'] = config.get('host', FLAGS.host)
    config['port'] = config.get('port', FLAGS.port)
    config['platform'] = config.get('platform', FLAGS.platform)
    config['storage_quota'] = config.get('storage_quota', FLAGS.storage_quota)


def main(argv):
    """
    The Entry of client agent that is the daemon process of client.
    The functions of this agent are communicate with server, receive training
    and evaluating task and run those task, return the result to server.

    args:
        argv: Unused.
    """
    del argv

    if const.STORAGE_TYPE.lower() == "s3":
        convert_s3_to_posix(const.WORKSPACE_BUCKET, const.S3_ENDPOINT,
                            const.S3_ACCESS_KEY, const.S3_SECRET_KEY,
                            const.WORKSPACE)

    config_dic = FLAGS.flag_values_dict()
    if FLAGS.config_file:
        config_dic = __parse_config_file(config_dic['config_file'])
        __set_default_value(config_dic)

    set_log(config_dic['log_level'])

    validate_agent_config(config_dic)

    client = Client(config_dic)
    asyncio.run(client.start())


if __name__ == '__main__':
    app.run(main)
