#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-many-instance-attributes, broad-except, no-member
# pylint:disable=too-many-arguments
"""SSA simple Server, woth one mask, used to generate mask and decrypt data.
"""
import asyncio
from collections import OrderedDict

from absl import logging

from neursafe_fl.python.utils.timer import Timer
from neursafe_fl.proto.secure_aggregate_grpc import SSAServiceStub
from neursafe_fl.proto.secure_aggregate_pb2 import PublicKeys, SSAMessage
from neursafe_fl.python.libs.secure.secure_aggregate.common import \
    ProtocolStage, PLAINTEXT_MULTIPLE, can_be_added
from neursafe_fl.python.libs.secure.secure_aggregate.ssa_controller import \
    ssa_controller
from neursafe_fl.python.trans.grpc_call import unary_call
from neursafe_fl.python.libs.secure.secure_aggregate.ssa_server import \
    SSABaseServer, SERVER, STAGE_TIME_INTERVAL


class SSASimpleServer(SSABaseServer):
    """Secret Share Aggregate, only use one mask, used to decrypt data.

    Args:
        handle: The unique string represents this encryption and decryption.
        min_client_num: Minimum number of clients required.
        client_num: Number of participating clients.
        wait_aggregate_interval: the time to wait for use descrypt.
        ssl_key:
        kwargs:
            stage_time_interval: the time to wait a stage timeout.
    """
    def __init__(self, handle, min_client_num, client_num,
                 wait_aggregate_interval,
                 ssl_key=None, **kwargs):
        super().__init__(handle, min_client_num, client_num, ssl_key)

        self.__stage_time_interval = kwargs.get("stage_time_interval",
                                                STAGE_TIME_INTERVAL)
        self.__wait_aggregate_interval = wait_aggregate_interval
        self.__wait_aggregate_timer = None

        self.__rpt_public_key_clients = []
        self.__rpt_masked_result_clients = []

        self.__public_keys = {}

        self.__stage = None
        self.__stage_timer = None
        self.__error = None

    def initialize(self):
        """Initialize.
        """
        ssa_controller.register_handler(self._handle,
                                        SERVER,
                                        self)
        self.__stage = ProtocolStage.ExchangePublicKey

        self.__start_wait_aggregate_timer()
        self.__start_stage_timer(self.__exchange_public_keys)

    def __clear(self):
        ssa_controller.unregister_handler(self._handle, SERVER)

    def __start_wait_aggregate_timer(self):
        self.__wait_aggregate_timer = Timer(
            self.__wait_aggregate_interval,
            self.__wait_aggregate_timeout)
        self.__wait_aggregate_timer.start()

    def __stop_wait_aggregate_timer(self):
        self.__wait_aggregate_timer.cancel()

    def __start_stage_timer(self, process_func):
        self.__stage_timer = Timer(self.__stage_time_interval, process_func)
        self.__stage_timer.start()

    def __stop_stage_timer(self):
        if self.__stage_timer:
            self.__stage_timer.cancel()

        self.__stage_timer = None

    def __wait_aggregate_timeout(self):
        error = 'Protocol stage %s timeout, wait time %ss' % (
            self.__stage, self.__wait_aggregate_interval)
        self.__process_error(error)

    def __process_error(self, error):
        if not self.__error:
            self.__error = error
            self.__clear()

    async def __handle_public_key(self, msg):
        self.__assert_stage(ProtocolStage.ExchangePublicKey)

        self.__save_public_key(msg.public_key_rpt)
        self.__rpt_public_key_clients.append(msg.public_key_rpt.client_id)

        if len(self.__rpt_public_key_clients) == self._client_num:
            self.__exchange_public_keys()

    def __save_public_key(self, public_key):
        self.__public_keys[public_key.client_id] = public_key

    def __exchange_public_keys(self):
        try:
            self.__stop_stage_timer()
            self.__stage = ProtocolStage.CiphertextAggregate

            msg = self.__encode_public_keys_msg()
            self.__broadcast_msg_to_clients(
                self.__public_keys, msg)
        except Exception as err:
            logging.exception(str(err))
            self.__process_error(str(err))

    def __encode_public_keys_msg(self):
        public_keys = PublicKeys()
        for public_key in self.__public_keys.values():
            public_keys.public_key.append(public_key)

        return SSAMessage(
            handle=self._handle,
            public_keys_bcst=public_keys)

    def __broadcast_msg_to_clients(self, client_list, msg):
        for alive_client_id in client_list:
            asyncio.create_task(self.__send_pks(alive_client_id, msg))

    async def __send_pks(self, client_id, msg):
        await unary_call(SSAServiceStub, 'call', msg,
                         client_id,
                         certificate_path=self._ssl_key,
                         metadata={"destination": client_id})

    def ciphertext_accumulate(self, data, client_id):
        """Accumulate partner's data, the data is ciphertext.

        Args:
            data: The data reported by client, which will be aggregated.
            client_id: which client report the data.
        """
        if self.__stage in (None, ProtocolStage.ExchangePublicKey):
            raise RuntimeError("Mask in client not ready, this time "
                               "use accumulate is wrong.")
        if self.__stage == ProtocolStage.DecryptResult:
            raise RuntimeError("Secure aggregate already in decrypt stage, "
                               "can not do accumulate.")
        self.__raise_exception_if_error()

        self._accumulate_data(data)

        self.__rpt_masked_result_clients.append(client_id)
        return self._total_data

    async def decrypt(self):
        """Decrypt the accumulated data.

        Return:
            The unmask accumulated data.
        """
        self.__assert_stage(ProtocolStage.CiphertextAggregate)
        self.__stop_wait_aggregate_timer()
        self.__assert_client_not_drop()
        self.__raise_exception_if_error()

        self.__stage = ProtocolStage.DecryptResult

        return self.__do_decrypt()

    def __do_decrypt(self):
        if isinstance(self._total_data, list):
            self.__decrypt_list()
        elif isinstance(self._total_data, OrderedDict):
            self.__decrypt_ordered_dict()
        elif can_be_added(self._total_data):
            self._total_data = self._total_data / PLAINTEXT_MULTIPLE
        else:
            raise TypeError('Not support data type %s' %
                            type(self._total_data))
        return self._total_data

    def __decrypt_list(self):
        for index, value in enumerate(self._total_data):
            self._total_data[index] = value / PLAINTEXT_MULTIPLE

    def __decrypt_ordered_dict(self):
        for name, value in self._total_data.items():
            self._total_data[name] = value / PLAINTEXT_MULTIPLE

    def __assert_client_not_drop(self):
        same_values = set(self.__rpt_public_key_clients) \
            & set(self.__rpt_masked_result_clients)

        if (len(same_values) < self._min_client_num
                or len(same_values) != len(self.__rpt_masked_result_clients)
                or len(same_values) != len(self.__rpt_public_key_clients)):
            raise RuntimeError("Some client drop before aggregate, "
                               "unable to complete decrypt.")

    def __assert_stage(self, stage):
        if self.__stage is not stage:
            raise RuntimeError("The message has timed out and the "
                               "stage is now in %s." % self.__stage)

    def __raise_exception_if_error(self):
        if self.__error:
            raise RuntimeError(self.__error)

    async def handle_msg(self, msg):
        """Process the ssa protocol message.
        """
        msg_handlers = {
            'public_key_rpt': self.__handle_public_key
        }

        which = msg.WhichOneof('spec')
        await msg_handlers[which](msg)
