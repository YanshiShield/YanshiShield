#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-many-instance-attributes
"""Round Controller Module."""
import time
import asyncio
from datetime import datetime

from absl import logging

from neursafe_fl.python.coordinator.client_selector import ClientSelector
from neursafe_fl.python.coordinator.common.types import RoundResult, \
    Statistics, ErrorCode
from neursafe_fl.python.coordinator.common.const import RETRY_TIMEOUT, \
    MAX_RETRY_TIMES
from neursafe_fl.python.coordinator.errors import (RoundFailedError,
                                                   RoundStoppedError,
                                                   DeviceNotEnoughError,
                                                   RemoteCallFailedError,
                                                   AggregationFailedError,
                                                   ExtendExecutionFailed)
from neursafe_fl.proto.message_pb2 import Status


class RoundController:
    """Round Controller controls the round process of federate learning.

    The main process of one round including:
        1. select clients
        2. broadcast task(params) to each client
        3. wait clients' reply
        4. aggregate the result
    Train, Evaluate .etc round shares the same process.
    Round Controller only focus on the process of one round, and also process
    any exception in this round.
    """

    def __init__(self, hyper, config):
        self.__timeout = hyper["round_timeout"]
        # broadcast clients number
        self.__max_num = hyper["client_num"]
        # upload clients number
        self.__threshold_num = hyper["threshold_client_num"]

        self.__client_selector = ClientSelector(config)
        self.__round = None

        self.__event = asyncio.Event()
        self.__timer = None
        self.__clients = None
        self.__received_reply = 0
        self.__success_reply = 0
        self.__failed_reply = 0

        self.__accept_updates = True
        self.__stopped = False
        self.__error_code = 0
        self.__error_msg = None

        self.__need_wait = config.get("need_wait", True)

    async def run(self, round_ins):
        """Run the round's main process.

        Args:
            round_ins: the round object, could be TrainRound or EvaluateRound.
                       This object will provide callbacks(BaseRound callback
                       functions) to process some data during the workflow.
        Returns:
            The RoundResult object, including all the execution status,
            results and statistics of this round.
        """
        self.__round = round_ins
        start_time = time.time()
        result = RoundResult()
        try:
            await self.__select_clients()
            await self.__broadcast_task_to_client()
            self.__start_monitor_timer()
            if self.__need_wait:
                await self.__wait_updates()
            status, values = await self.__finish()
            result.status = status
            result.delta_weights = values.get("weights")
            result.metrics = values.get("metrics")

        except (DeviceNotEnoughError, RoundFailedError, RoundStoppedError,
                AggregationFailedError) as err:
            logging.exception(str(err))
            result.status = False
            result.code = self.__error_code
            result.reason = str(err)
        end_time = time.time()
        logging.info("%s execute status: %s, using time: %.2fs",
                     self.__round.__class__.__name__,
                     result.status, end_time - start_time)
        await self.__client_selector.release()
        result.statistics = self.__calculate_statistics(end_time - start_time)
        return result

    async def __select_clients(self):
        """Select clients for this round.
        """
        demands = {"client_num": self.__max_num}
        self.__clients = await self.__client_selector.select(demands)
        logging.info("Select clients success, %s", self.__clients)

    async def __broadcast_task_to_client(self):
        """Broadcast params to each client in this round."""
        self.__round.on_prepare()

        send_tasks = []
        for client in self.__clients:
            send_tasks.append(
                asyncio.create_task(self.__round.on_broadcast(client)))

        success_count = 0
        for send_task in send_tasks:
            try:
                await send_task
                success_count += 1
            except RemoteCallFailedError as err:
                logging.warning(str(err))
        if success_count < self.__threshold_num:
            raise RoundFailedError("Available clients %s less than the "
                                   "threshold %s" % (success_count,
                                                     self.__threshold_num))

    def __start_monitor_timer(self):
        """Set the timeout timer of the round.

        When round timeout, if not received enough client's reply, this round
        failed.
        """
        loop = asyncio.get_running_loop()
        self.__timer = loop.call_later(self.__timeout, self.__timeout_handler)
        format_time = datetime.fromtimestamp(time.time() + self.__timeout)
        logging.info("Start round timer, timeout time %s", format_time)

    def __timeout_handler(self):
        self.__timer = None
        self.__event.set()
        logging.error("Round failed, reason: timeout.")

    async def __wait_updates(self):
        """Wait for clients to upload its updates.

        When round timeout or already received enough updates, will trigger
        the event to breakout.
        """
        logging.info("Start waiting for %sing...",
                     self.__round.__class__.__name__)
        while True:
            if (self.__success_reply < self.__threshold_num
                    and self.__received_reply < self.__max_num
                    and self.__timer is not None) and not self.__stopped:
                await self.__event.wait()
                self.__event.clear()
            else:
                if self.__timer:
                    self.__timer.cancel()
                break

        self.__accept_updates = False

    async def __finish(self):
        """Process all the clients' updates.
        """
        if self.__stopped:
            await self.__stop_clients(self.__clients)
            raise RoundStoppedError(self.__error_msg)

        if self.__timer is None or self.__success_reply < self.__threshold_num:
            status, result = False, self.__abnormal_finish()
        else:
            status = True
            result = await self.__normal_finish()
        return status, result

    async def __stop_clients(self, clients, retry_times=1):
        stop_tasks = []
        for client in clients:
            task = asyncio.create_task(self.__round.on_stop(client))
            stop_tasks.append((client, task))

        stop_failed_clients = await self.__waiting_for_stop(stop_tasks)
        if stop_failed_clients and retry_times < MAX_RETRY_TIMES:
            await asyncio.sleep(RETRY_TIMEOUT)
            logging.info("Retry %s to stop clients %s",
                         retry_times, stop_failed_clients)
            await self.__stop_clients(stop_failed_clients, retry_times + 1)

    async def __waiting_for_stop(self, tasks):
        failed = []
        for item in tasks:
            client, task = item[0], item[1]
            try:
                await task
            except RemoteCallFailedError as err:
                logging.warning("Broadcast stop client failed %s", str(err))
                failed.append(client)
        return failed

    async def __normal_finish(self):
        logging.info("Round receive enough success message %s",
                     self.__success_reply)
        if self.__timer:
            self.__timer.cancel()
        return await self.__round.on_finish()

    def __abnormal_finish(self):
        raise RoundFailedError("Round receive success message %s less than "
                               "requirement %s" % (self.__success_reply,
                                                   self.__threshold_num))

    async def stop(self):
        """Stop the round.

        The stop command will force the client to stop federate job.
        """
        err_msg = "Force to stop federate job round success."
        self.__stop(ErrorCode.ForceStop, err_msg)

    def __stop(self, code, reason):
        self.__error_code = code
        self.__error_msg = reason
        self.__stopped = True
        self.__event.set()

    async def process_msg(self, msg):
        """Process messages(updates) belong to this round.

        Args:
            msg: client's uploaded message of this round. Format is proto.
        """
        params = msg[0]
        if params.status == Status.success:
            if self.__accept_updates:
                await self.__try_to_aggregate(msg)
            else:
                logging.warning("Received timeout message: %s", msg)
                self.__failed_reply += 1
        else:
            logging.warning("Received %s message: %s", params.status, msg)
            self.__failed_reply += 1

        self.__received_reply += 1
        logging.info("Round already receive message num %s",
                     self.__received_reply)
        self.__event.set()

    async def __try_to_aggregate(self, msg):
        message_number = self.__success_reply + self.__failed_reply
        try:
            await self.__round.on_aggregate(msg, number=message_number)
            self.__success_reply += 1
            logging.info("Aggregate msg number %s success.", message_number)
        except ExtendExecutionFailed as err:
            self.__stop(ErrorCode.ExtendFailed, str(err))
        except Exception as err:  # pylint:disable=broad-except
            self.__failed_reply += 1
            logging.exception("Aggregate msg number %s failed, reason: %s",
                              message_number, str(err))

    def __calculate_statistics(self, total_time):
        stats = Statistics()
        stats.success = self.__success_reply
        stats.failed = self.__failed_reply
        stats.spend_time = total_time
        return stats
