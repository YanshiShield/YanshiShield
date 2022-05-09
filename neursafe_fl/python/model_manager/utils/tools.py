#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Utils for model manager.
"""

import sys
import time
from absl import logging


def current_time():
    """Return current format time.
    """
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def abnormal_exit(msg):
    """The model manager exit with error.
    """
    logging.error("The program exit with error: %s", msg)
    sys.exit(1)
