#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-many-instance-attributes, too-many-arguments, broad-except
# pylint:disable=no-member, unused-argument
"""SSA Client, with one mask, used to generate mask and encrypt data.
"""
import asyncio

from absl import logging

from neursafe_fl.python.utils.timer import Timer
from neursafe_fl.proto.secure_aggregate_grpc import SSAServiceStub
from neursafe_fl.proto.secure_aggregate_pb2 import SSAMessage, PublicKey
from neursafe_fl.python.libs.secure.secure_aggregate.common import \
    ProtocolStage, PseudorandomGenerator
from neursafe_fl.python.libs.secure.secure_aggregate.dh import DiffieHellman
from neursafe_fl.python.libs.secure.secure_aggregate.ssa_controller import \
    ssa_controller
import neursafe_fl.python.trans.grpc_call as grpc_call
from neursafe_fl.python.libs.secure.secure_aggregate.ssa_client import \
    SSABaseClient


class SSASimpleClient(SSABaseClient):
    """Secret Share Aggregate, used to generate one mask and encrypt data.

    Args:
        handle: The unique string represents this encryption and decryption.
        server_addr: server address, like: ip:port.
        ssl_key: the ssl path to use GRPCS.
        client_id: the client id.
        min_client_num: Minimum number of clients required.
        client_num: Number of participating clients.
        use_same_mask: Whether to use the same mask. True mean all weights
            use a ame mask, False mean use different mask in different
            layers in weights.
        grpc_metadata: the metadata which will set in grpc hearder.
        ready_timer_interval: the timeout wait for mask generated.
        server_aggregate_interval:  the time to wait for server to use decrypt.
        kwargs:
            stage_time_interval: the time to wait a stage timeout.
    """
    def __init__(self, handle, server_addr, ssl_key, client_id,
                 min_client_num, client_num, use_same_mask,
                 grpc_metadata=None,
                 ready_timer_interval=60, **kwargs):
        super().__init__(handle, server_addr, ssl_key, client_id,
                         min_client_num, client_num, use_same_mask,
                         grpc_metadata)

        self.__ready_timer_interval = ready_timer_interval
        self.__ready_timer = None
        self.__ready_event = asyncio.Event()

        self.__stage = None
        self.__error = None

        self.__dh = DiffieHellman()
        self.__my_dh_keys = {}
        self.__dh_public_keys = {}

    def initialize(self):
        """Initialize client.
        """
        ssa_controller.register_handler(self._handle,
                                        self._my_id,
                                        self)

        self.__start_ready_timer()
        asyncio.create_task(self.__start())

    def __clear(self):
        ssa_controller.unregister_handler(self._handle, self._my_id)

    def __start_ready_timer(self):
        self.__ready_timer = Timer(self.__ready_timer_interval,
                                   self.__process_error)
        self.__ready_timer.start("Ready wait timeout, wait time %ss." %
                                 self.__ready_timer_interval)

    def __stop_ready_timer(self):
        if self.__ready_timer:
            self.__ready_timer.cancel()

    def __process_error(self, error):
        if not self.__error:
            self.__error = error
            self.__ready_event.set()
            self.__clear()

    async def __start(self):
        self.__stage = ProtocolStage.ExchangePublicKey
        try:
            await self.__exchange_public_key()
        except Exception as err:
            logging.exception(str(err))
            self.__process_error(str(err))

    async def __exchange_public_key(self):
        self.__generate_self_key()
        await self.__report_self_key_to_server()

    def __generate_self_key(self):
        (self.__my_dh_keys['s_sk'],
         self.__my_dh_keys['s_pk']) = self.__dh.generate()

    async def __report_self_key_to_server(self):
        msg = self.__encode_public_key()
        await self.__send_msg_to_server(msg)

    def __encode_public_key(self):
        return SSAMessage(
            handle=self._handle,
            public_key_rpt=PublicKey(
                client_id=self._my_id,
                s_pk=str(self.__my_dh_keys['s_pk'])))

    async def __send_msg_to_server(self, msg):
        await grpc_call.unary_call(
            SSAServiceStub, 'call', msg,
            self._server_addr,
            certificate_path=self._ssl_key,
            metadata=self._grpc_metadata)

    def __handle_public_keys(self, msg):
        try:
            self.__assert_stage(ProtocolStage.ExchangePublicKey)
            self.__assert_number(len(msg.public_keys_bcst.public_key))

            self.__save_public_keys(msg.public_keys_bcst)

            asyncio.create_task(self.__generate_mask())
        except Exception as err:
            logging.exception(str(err))
            self.__process_error(str(err))
            raise err

    def __assert_stage(self, stage):
        if self.__stage is not stage:
            raise RuntimeError("The message has timed out and the "
                               "stage is now in %s." % self.__stage)

    def __assert_number(self, number):
        if number < self._min_client_num:
            raise ValueError('The number of surviving clients is '
                             'less than client number, %s/%s.' % (
                                 number, self._client_num))

    def __save_public_keys(self, public_keys):
        for public_key in public_keys.public_key:
            if public_key.client_id == self._my_id:
                continue
            self.__dh_public_keys[public_key.client_id] = public_key

    async def __generate_mask(self):
        for v_id, v_public_key in self.__dh_public_keys.items():
            s_uv = self.__dh.agree(
                self.__my_dh_keys['s_sk'],
                int(v_public_key.s_pk))
            self._s_uv_s.append((v_id, PseudorandomGenerator(s_uv)))

        self.__ready_event.set()
        self.__stage = ProtocolStage.CiphertextAggregate

    async def wait_ready(self):
        """Wait initialize ready.
        """
        await self.__ready_event.wait()

        self.__raise_exception_if_error()

    def encrypt(self, data):
        """Use double mask to encrypt data.

        Note: you must call wait_mask_generated first,
            or maybe double mask not ready.

        Args:
            data: the plaintext used to encrypt. supported type:
                [int, float, and iterable value ].

        return:
            The encrypted data.
        """
        self.__raise_exception_if_error()
        self.__assert_stage(ProtocolStage.CiphertextAggregate)

        new_data = self._do_encrypt(data)

        self.__stop_ready_timer()
        self.__clear()
        self.__stage = ProtocolStage.DecryptResult
        return new_data

    def __raise_exception_if_error(self):
        if self.__error:
            raise RuntimeError(self.__error)

    def handle_msg(self, msg):
        """Handle message from server.
        """
        msg_handlers = {
            'public_keys_bcst': self.__handle_public_keys
        }

        which = msg.WhichOneof('spec')
        msg_handlers[which](msg)
