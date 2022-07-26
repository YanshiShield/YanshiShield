#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-many-instance-attributes, too-many-arguments, broad-except
# pylint:disable=no-member, invalid-name
"""SSA Client, used to generate mask and encrypt data.
"""
import abc
import asyncio
from collections import OrderedDict
import random

from absl import logging
from secretsharing import SecretSharer
import numpy as np

from neursafe_fl.python.utils.timer import Timer
from neursafe_fl.proto.secure_aggregate_grpc import SSAServiceStub
from neursafe_fl.proto.secure_aggregate_pb2 import SSAMessage, PublicKey,\
    EncryptedShares, EncryptedShare, SecretShares, SecretShare
from neursafe_fl.python.libs.secure.secure_aggregate.aes import \
    encrypt_with_gcm, decrypt_with_gcm
from neursafe_fl.python.libs.secure.secure_aggregate.common import \
    ProtocolStage, can_be_added, PseudorandomGenerator
from neursafe_fl.python.libs.secure.secure_aggregate.dh import DiffieHellman
from neursafe_fl.python.libs.secure.secure_aggregate.ssa_controller import \
    ssa_controller
from neursafe_fl.python.libs.secure.secure_aggregate.ssa_server import SERVER
import neursafe_fl.python.trans.grpc_call as grpc_call


MIN_B_MASK = 10000000000
MAX_B_MASK = 9999999999999999
ENCRYPTED_SHARE_DELIMITER = '$$'
STAGE_TIME_INTERVAL = 60


class SSABaseClient:
    """Secret Share Aggregate, base client"""
    def __init__(self, handle, server_addr, ssl_key, client_id,
                 min_client_num, client_num, use_same_mask,
                 grpc_metadata):
        self._handle = handle
        self._my_id = client_id
        self._server_addr = server_addr
        self._use_same_mask = use_same_mask
        self._ssl_key = ssl_key

        self._grpc_metadata = {"destination": SERVER}
        if grpc_metadata:
            self._grpc_metadata.update(grpc_metadata)

        self._min_client_num = min_client_num
        self._client_num = client_num

        self._b = None
        self._s_uv_s = []

    @abc.abstractmethod
    def initialize(self):
        """Initialize client."""

    @abc.abstractmethod
    async def wait_ready(self):
        """Wait initialize ready.
        """

    @abc.abstractmethod
    def encrypt(self, data):
        """Use mask to encrypt data."""

    @abc.abstractmethod
    def handle_msg(self, msg):
        """Handle message from server.
        """

    def _do_encrypt(self, data):
        if isinstance(data, list):
            # tf's weights is list, the value is ndarray
            new_data = self.__encrypt_list(data)
        elif isinstance(data, OrderedDict):
            # pytorch's value in OrderedDict, the value is torch.Tensor
            new_data = self.__encrypt_ordered_dict(data)
        elif can_be_added(data):
            masks = self._genernate_masks(1)
            new_data = np.add(data, masks[0])
        else:
            raise TypeError('Not support data type %s' % type(data))
        return new_data

    def __encrypt_list(self, data):
        new_data = []
        if not self._use_same_mask:
            masks = self._genernate_masks(len(data))
            for index, item in enumerate(data):
                new_data.append(np.add(item, masks[index]))
        else:
            masks = self._genernate_masks(1)
            for item in data:
                new_data.append(np.add(item, masks[0]))
        return new_data

    def __encrypt_ordered_dict(self, data):
        new_data = OrderedDict()
        if not self._use_same_mask:
            masks = self._genernate_masks(len(data))
            for index, (name, value) in enumerate(data.items()):
                new_data[name] = np.add(value, masks[index])
        else:
            masks = self._genernate_masks(1)
            for name, value in data.items():
                new_data[name] = np.add(value, masks[0])
        return new_data

    def _genernate_masks(self, data_size):
        if self._b:
            b_prg = PseudorandomGenerator(self._b)
        else:
            b_prg = None

        masks = []
        for _ in range(data_size):
            s_total = 0
            for (v_id, s_uv_prg) in self._s_uv_s:
                if self._my_id > v_id:
                    s_total += s_uv_prg.next_number()
                else:
                    s_total -= s_uv_prg.next_number()

            if b_prg:
                masks.append(b_prg.next_number() + s_total)
            else:
                masks.append(s_total)
        logging.debug('masks %s', masks)
        return masks


class SSAClient(SSABaseClient):
    """Secret Share Aggregate, used to generate mask and encrypt data.

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
                 ready_timer_interval=60,
                 server_aggregate_interval=90,
                 **kwargs):
        super().__init__(handle, server_addr, ssl_key, client_id,
                         min_client_num, client_num, use_same_mask,
                         grpc_metadata)

        self.__stage_time_interval = kwargs.get("stage_time_interval",
                                                STAGE_TIME_INTERVAL)
        self.__ready_timer_interval = ready_timer_interval
        self.__ready_timer = None
        self.__ready_event = asyncio.Event()

        self.__server_aggregate_interval = server_aggregate_interval
        self.__server_aggregate_timer = None

        self.__stage = None
        self.__stage_timer = None
        self.__error = None

        self.__dh = DiffieHellman()
        self.__my_dh_keys = {}
        self.__dh_public_keys = {}

        self.__my_b_share = None
        self.__encrypted_shares = None

    def initialize(self):
        """Initialize client.
        """
        ssa_controller.register_handler(self._handle,
                                        self._my_id,
                                        self)

        self.__start_ready_timer()
        self.__start_server_aggregate_timer()
        asyncio.create_task(self.__start())

    def __clear(self):
        ssa_controller.unregister_handler(self._handle, self._my_id)

    def __start_ready_timer(self):
        self.__ready_timer = Timer(self.__ready_timer_interval,
                                   self.__staget_timeout)
        self.__ready_timer.start("Ready wait timeout, wait time %ss." %
                                 self.__ready_timer_interval)

    def __stop_ready_timer(self):
        if self.__ready_timer:
            self.__ready_timer.cancel()

    def __set_ready(self):
        self.__ready_event.set()

    def __start_server_aggregate_timer(self):
        self.__server_aggregate_timer = Timer(self.__server_aggregate_interval,
                                              self.__staget_timeout)
        self.__server_aggregate_timer.start(
            "Aggregate wait timeout, wait time %ss." %
            self.__server_aggregate_interval)

    def __stop_server_aggregate_timer(self):
        self.__server_aggregate_timer.cancel()

    def __start_stage_timer(self):
        self.__stage_timer = Timer(self.__stage_time_interval,
                                   self.__staget_timeout)
        self.__stage_timer.start(
            "Protocol stage %s timeout, wait stage time %ss" % (
                self.__stage, self.__stage_time_interval))

    def __stop_stage_timer(self):
        if self.__stage_timer:
            self.__stage_timer.cancel()

        self.__stage_timer = None

    def __staget_timeout(self, error_msg):
        self.__process_error(error_msg)

    def __process_error(self, error):
        if not self.__error:
            self.__error = error
            self.__ready_event.set()
            self.__clear()

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
        self.__stage = ProtocolStage.DecryptResult
        return new_data

    async def __start(self):
        self.__stage = ProtocolStage.ExchangePublicKey
        try:
            await self.__exchange_public_key()
        except Exception as err:
            logging.exception(str(err))
            self.__process_error(str(err))

    async def __exchange_public_key(self):
        self.__start_stage_timer()
        self.__generate_self_key()
        await self.__report_self_key_to_server()

    def __generate_self_key(self):
        (self.__my_dh_keys['c_sk'],
         self.__my_dh_keys['c_pk']) = self.__dh.generate()
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
                s_pk=str(self.__my_dh_keys['s_pk']),
                c_pk=str(self.__my_dh_keys['c_pk'])))

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
            self.__stop_stage_timer()

            self.__save_public_keys(msg.public_keys_bcst)

            asyncio.create_task(self.__exchange_encrypted_share())
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
                             'less than threshold, %s/%s.' % (
                                 number, self._min_client_num))

    def __save_public_keys(self, public_keys):
        for public_key in public_keys.public_key:
            if public_key.client_id == self._my_id:
                continue
            self.__dh_public_keys[public_key.client_id] = public_key

    async def __exchange_encrypted_share(self):
        self.__stage = ProtocolStage.ExchangeEncryptedShare
        self.__start_stage_timer()

        b_shares, s_sk_shares = self.__generate_secret_shares()
        encrypted_shares = self.__encrypt_shares(b_shares, s_sk_shares)
        msg = self.__encode_encrypted_shares_msg(encrypted_shares)
        await self.__send_encrypted_shares(msg)

    async def __send_encrypted_shares(self, msg):
        await self.__send_msg_to_server(msg)

    def __generate_secret_shares(self):
        self.__generate_b_mask()
        b_shares = self.__split_b_mask()
        s_sk_shares = self.__split_s_mask()
        self.__save_my_b_share(b_shares)

        return b_shares, s_sk_shares

    def __generate_b_mask(self):
        self._b = random.randint(MIN_B_MASK, MAX_B_MASK)

    def __split_b_mask(self):
        return SecretSharer.split_secret(
            str(self._b), self._min_client_num, self._client_num)

    def __split_s_mask(self):
        return SecretSharer.split_secret(
            str(self.__my_dh_keys['s_sk']), self._min_client_num,
            self._client_num)

    def __save_my_b_share(self, b_shares):
        self.__my_b_share = b_shares[-1]

    def __encrypt_shares(self, b_shares, s_sk_shares):
        encrypted_shares = EncryptedShares(client_id=self._my_id)
        for index, (client_id, public_key) in enumerate(
                self.__dh_public_keys.items()):
            aes_key = self.__dh.agree(self.__my_dh_keys['c_sk'],
                                      int(public_key.c_pk))
            msg = ''.join([
                str(self._my_id), ENCRYPTED_SHARE_DELIMITER, str(client_id),
                ENCRYPTED_SHARE_DELIMITER, s_sk_shares[index],
                ENCRYPTED_SHARE_DELIMITER, b_shares[index]])

            encrypted_share = encrypt_with_gcm(aes_key, msg,
                                               self._handle, self._my_id)

            encrypted_shares.encrypted_share.append(
                EncryptedShare(client_id=client_id, data=encrypted_share))
        return encrypted_shares

    def __encode_encrypted_shares_msg(self, encrypted_shares):
        return SSAMessage(
            handle=self._handle,
            encrypted_shares_rpt=encrypted_shares)

    def __handle_encrypted_shares(self, msg):
        try:
            self.__assert_stage(ProtocolStage.ExchangeEncryptedShare)
            self.__assert_number(
                len(msg.encrypted_shares_bcst.encrypted_share) + 1)
            self.__stop_stage_timer()

            self.__save_encrypted_shares(msg.encrypted_shares_bcst)

            asyncio.create_task(self.__generate_double_mask())
        except Exception as err:
            logging.exception(str(err))
            self.__process_error(str(err))
            raise err

    def __save_encrypted_shares(self, encrypted_shares):
        self.__encrypted_shares = encrypted_shares

    async def __generate_double_mask(self):
        for encrypted_share in self.__encrypted_shares.encrypted_share:
            if self._my_id == encrypted_share.client_id:
                continue

            v_id = encrypted_share.client_id
            s_uv = self.__dh.agree(
                self.__my_dh_keys['s_sk'],
                int(self.__dh_public_keys[v_id].s_pk))
            self._s_uv_s.append((v_id, PseudorandomGenerator(s_uv)))

        self.__stage = ProtocolStage.CiphertextAggregate
        self.__set_ready()

    def __handle_alive_clients(self, msg):
        try:
            self.__assert_stage(ProtocolStage.DecryptResult)
            self.__assert_number(len(msg.alive_clients_bcst.client_id))
            self.__stop_server_aggregate_timer()

            asyncio.create_task(
                self.__process_alive_clients(msg.alive_clients_bcst))

        except Exception as err:
            logging.exception(str(err))
            self.__process_error(str(err))
            raise err

    async def __process_alive_clients(self, alive_clients):
        try:
            secret_shares = self.__take_out_shares(alive_clients)
            msg = self.__encode_secret_shares_msg(secret_shares)
            await self.__send_secret_shares(msg)
        finally:
            self.__clear()

    async def __send_secret_shares(self, msg):
        await self.__send_msg_to_server(msg)

    def __take_out_shares(self, alive_clients):
        secret_shares = SecretShares()
        for encrypted_share in self.__encrypted_shares.encrypted_share:
            shares = self.__decrypt_shares(encrypted_share)
            _, _, s_sk_share, b_share = shares.split('$$')

            if encrypted_share.client_id in alive_clients.client_id:
                secret_shares.b_share.append(SecretShare(
                    client_id=encrypted_share.client_id, data=b_share))
            else:
                secret_shares.s_sk_share.append(SecretShare(
                    client_id=encrypted_share.client_id, data=s_sk_share))

        self.__add_my_b_share(secret_shares)

        return secret_shares

    def __add_my_b_share(self, secret_shares):
        secret_shares.b_share.append(
            SecretShare(client_id=self._my_id,
                        data=self.__my_b_share))

    def __decrypt_shares(self, encrypted_share):
        client_id = encrypted_share.client_id
        aes_key = self.__dh.agree(self.__my_dh_keys['c_sk'],
                                  int(self.__dh_public_keys[client_id].c_pk))
        return decrypt_with_gcm(aes_key, encrypted_share.data,
                                self._handle, client_id)

    def __encode_secret_shares_msg(self, secret_shares):
        return SSAMessage(
            handle=self._handle,
            secret_shares_rpt=secret_shares)

    def __raise_exception_if_error(self):
        if self.__error:
            raise RuntimeError(self.__error)

    def handle_msg(self, msg):
        """Handle message from server.
        """
        msg_handlers = {
            'public_keys_bcst': self.__handle_public_keys,
            'encrypted_shares_bcst': self.__handle_encrypted_shares,
            'alive_clients_bcst': self.__handle_alive_clients
        }

        which = msg.WhichOneof('spec')
        msg_handlers[which](msg)
