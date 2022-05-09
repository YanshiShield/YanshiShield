#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""setup log config
"""

import logging as build_in_logging
from absl import logging
from absl.logging import PythonFormatter


FORMAT = ("[%(asctime)s] %(filename)s"
          "[line:%(lineno)d] %(levelname)s: %(message)s")


class CustomPythonFormatter(PythonFormatter):
    """Custom log format
    """
    def format(self, record):
        return super(PythonFormatter,  # pylint:disable=bad-super-call
                     self).format(record)


def set_log(level='debug'):
    """Setup log format

    Args:
        level: Use to set log level. Legal string values are 'debug', 'info',
        'warning', 'error', and 'fatal' and case-insensitive. Default value
        is 'debug'.
    """
    logging.get_absl_handler().setFormatter(CustomPythonFormatter(fmt=FORMAT))

    logging.set_verbosity(level)


def set_buildin_log(level='DEBUG'):
    """Setup build-in log format.

    Args:
        level: Use to set log level. Legal string values are 'DEBUG', 'INFO',
        'WARNING', 'ERROR', and 'FATAL' and case-insensitive. Default value
        is 'DEBUG'.
    """
    build_in_logging.basicConfig(format=(FORMAT), level=level)
