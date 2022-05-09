#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Define data 'struct' for federated learning process."""


class RoundResult:  # pylint:disable=too-few-public-methods
    """Result struct definition for round.

    Struct contains detailed execution information: status, statistical
    information, results, error info etc.
    """
    def __init__(self):
        self.status = None  # bool
        self.delta_weights = None  # model weights according runtime
        self.metrics = None  # proto message
        self.statistics = None  # Statistics
        self.reason = None  # string
        self.code = 0


class ErrorCode:
    """Define error code of round.
    """
    ForceStop = 1
    ExtendFailed = 2


class Statistics:
    """Job or Round Statistics.

    Contains statistics of federated job and round, which indicates
    the execution status of federated training or one round.
    """
    def __init__(self):
        self.success = 0  # int
        self.failed = 0  # int
        self.spend_time = 0  # float
        self.progress = 0  # float

    def __str__(self):
        return "| Rounds | Success round | Failed round |  Time(s) |\n" \
               "|   %s   |      %s      |      %s      |   %.2f   |" % \
               (self.total, self.success, self.failed, self.spend_time)

    @property
    def total(self):
        """Get the total number."""
        return self.success + self.failed

    def increase_success(self):
        """Increase the success number."""
        self.success += 1

    def increase_failed(self):
        """Increase the failed number."""
        self.failed += 1

    def increase_spend_time(self, time):
        """Increase the spending time."""
        self.spend_time += time

    def calculate_progress(self, current, total):
        """Calculate the progress."""
        self.progress = round(100 * (current / total), 2)

    def dump(self):
        """Serialize to file."""
        # dump stats to record file.
