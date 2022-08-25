#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Server Entry Point."""
import asyncio

from absl import app
from absl import flags
from absl import logging
from neursafe_fl.python.utils.log import set_log

from neursafe_fl.python.coordinator.coordinator import Coordinator
from neursafe_fl.python.coordinator.validations import validate_config
import neursafe_fl.python.coordinator.common.const as const
from neursafe_fl.python.utils.s3_conversion import convert_s3_to_posix


FLAGS = flags.FLAGS

flags.DEFINE_string('job_name', 'default', 'Job name, the federated job name.')
flags.DEFINE_string('description', 'Federate Learning', 'Add detailed '
                                                        'instructions for this '
                                                        'job.')
flags.DEFINE_string('output', '', 'Job result output directory, such as the '
                                  'checkpoints, final model etc. will be saved '
                                  'in this directory. Default is under current'
                                  'work dir.')
flags.DEFINE_string('host', '0.0.0.0', 'IP address to serve for gRPC API.')
flags.DEFINE_integer('port', 50051, 'Port to listen on for gRPC API, the range '
                                    'is 1024~65535. Default port is 55051.',
                     lower_bound=1024, upper_bound=65535)
flags.DEFINE_string('clients', None,
                    'Config clients to participate in this job. Using ip:port '
                    'to represent one client service address, split by ",". '
                    'For example: 1 client "127.0.0.1:8888"'
                    '             2 clients "127.0.0.1:8888, 192.0.0.1:7777"')
flags.DEFINE_string('task_entry', None,
                    'Client Task entry point, used to specify task name to '
                    'client. Typically is the script entry point name of '
                    'the training task.')
flags.DEFINE_string('model_path', None,
                    'Local path of model, Which is the initial global '
                    'model to broadcast to client for training. Also, the '
                    'training results will be saved under this path.')
flags.DEFINE_string('runtime', None,
                    'Model runtime used for loading and training model. '
                    'Allowed model runtime: (tensorflow, pytorch). '
                    'More runtimes will be supported in future versions.')
flags.DEFINE_string('log_level', 'INFO',
                    'Log level, support [DEBUG, INFO, WARNING, ERROR].')
flags.DEFINE_string('ssl', None,
                    'If use gRPCs, you must set the ssl path, This is a path '
                    'where should have 3 files:\n'
                    '  cert.pem: saved certificate\n'
                    '  private.key: saved private key\n'
                    '  trusted.pem: saved trusted certificate, which will be '
                    "the coordinator's certificate.")
flags.DEFINE_string('config_file', None,
                    'Path to configuration file. More detailed configuration '
                    'can be configured in the configuration file, such as '
                    'hyper parameters, algorithms .etc'
                    'If used, configured args above will be replaced if the '
                    'configuration file contains the same args.'
                    'Please read the documentation for more details or '
                    'refer to the template in the examples.')


def main(argv):
    """The Entry of coordinator process."""
    del argv  # Unused

    config_dic = FLAGS.flag_values_dict()
    set_log(config_dic["log_level"])
    logging.debug("Load configuration: %s", config_dic)

    if const.STORAGE_TYPE.lower() == "s3":
        convert_s3_to_posix(const.WORKSPACE_BUCKET, const.S3_ENDPOINT,
                            const.S3_ACCESS_KEY, const.S3_SECRET_KEY,
                            const.COORDINATOR_WORKSPACE_PATH)

    valid_config = validate_config(config_dic)
    coordinator = Coordinator(valid_config)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(coordinator.start())


if __name__ == '__main__':
    app.run(main)
