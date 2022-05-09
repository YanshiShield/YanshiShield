#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
job scheduler exit abnormally
"""

import sys
from absl import logging


def exit_abnormally(err_msg):
    """
    Program exit abnormally and log out error message.
    """
    logging.error("Program exit abnormally: %s", err_msg)
    sys.exit(1)
