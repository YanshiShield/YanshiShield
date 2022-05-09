#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""FL Logger

used for save model processing、 training log and error log.
the log saved in task workspace. those log maybe send to server.
"""

import os

_LOG_FILE_NAME = 'fl.log'
_ERROR_FILE_NAME = 'error.log'


class FLLogger:
    """FL Logger, to log task's info/error log.
    """
    def __init__(self, task_workspace):
        self.__logfile = os.path.join(task_workspace, _ERROR_FILE_NAME)
        self.__log_stream = open(self.__logfile, 'ab')

    def close(self):
        """Close log stream.
        """
        if self.__log_stream:
            self.__log_stream.flush()
            self.__log_stream.close()
            self.__log_stream = None

    def error(self, message):
        """Logged error message.

        Args:
            message: Append message to error log file.
        """
        self.__log_stream.write(message)
