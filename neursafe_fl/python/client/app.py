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


DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 22000

flags.DEFINE_string('host', DEFAULT_HOST, 'Client listen host.')
flags.DEFINE_integer('port', DEFAULT_PORT, 'Client listen port.')
flags.DEFINE_string('server', None,
                    'The address of server, like ip:port where report the'
                    ' the train or evaluate result.')
flags.DEFINE_string('lmdb_path', None,
                    'LMDB path, an exist path, used save task metadata '
                    'and status.')
flags.DEFINE_string('workspace', None,
                    "Client's workspace path, where will be saved some"
                    ' temporary files. These temporary files are generated '
                    'when the task is running, such as weights、task result, '
                    'etc.')
flags.DEFINE_string('platform', "linux",
                    'Client run on some platform, support %s.'
                    % SUPPORT_PLATFORM)
flags.DEFINE_string('task_config_entry', None,
                    'This is a path of task config entry. in this path, some '
                    'task_config.json must be exist. The task_config.json '
                    'indicate the path of the script that the task runs、 '
                    ' the task command, etc.')
flags.DEFINE_integer('storage_quota', 1024,
                     'The storage quota of client (MB), which specified the '
                     'limit of Workspace, where will be generated '
                     'temporary files in task running. When storage_quota is '
                     'exceeded, the long-standing temporary files in Workspace'
                     ' will be deleted.')
flags.DEFINE_string('log_level', 'INFO',
                    'Log level, support [DEBUG, INFO, WARNING, ERROR].')
flags.DEFINE_string('ssl', None,
                    'If used GRPCS must set this, else not. This is a path '
                    'where should have 3 files:\n'
                    'cert.pem: saved certificate\n'
                    'private.key: saved private key\n'
                    'trusted.pem: saved trusted certificate, which will be '
                    "coordinator's certificate in")
flags.DEFINE_string('datasets', None,
                    'A JSON file path, the file describes the mapping '
                    'relationship between dataset name and dataset path.')
flags.DEFINE_string('config_file', None,
                    'Config file used when start client agent. (If used, '
                    'all other args are ignored. All needed args should '
                    'be configured in config file.)')

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
