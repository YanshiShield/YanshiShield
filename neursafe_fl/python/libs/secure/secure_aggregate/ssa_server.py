#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-many-instance-attributes, broad-except, no-member
# pylint:disable=too-many-arguments, invalid-name
"""SSA Server, used to generate mask and decrypt data.
"""
import abc
import asyncio
from collections import OrderedDict

import numpy as np
from absl import logging
from secretsharing import SecretSharer

from neursafe_fl.python.libs.secure.secure_aggregate.common import \
    ProtocolStage, can_be_added, PseudorandomGenerator
from neursafe_fl.python.libs.secure.secure_aggregate.dh import DiffieHellman
from neursafe_fl.python.libs.secure.secure_aggregate.ssa_controller import \
    ssa_controller
from neursafe_fl.python.utils.timer import Timer
from neursafe_fl.proto.secure_aggregate_grpc import SSAServiceStub
from neursafe_fl.proto.secure_aggregate_pb2 import PublicKeys, SSAMessage, \
    EncryptedShare, EncryptedShares, Clients
from neursafe_fl.python.trans.grpc_call import unary_call

STAGE_TIME_INTERVAL = 60
SERVER = 'server'


class SSABaseServer:
    """Secret Share Aggregate, base server"""
    def __init__(self, handle, min_client_num, client_num, use_same_mask,
                 ssl_key):
        self._handle = handle
        self._min_client_num = min_client_num
        self._client_num = client_num
        self._use_same_mask = use_same_mask
        self._ssl_key = ssl_key

        self._total_data = 0
        self._b_masks = []
        self._s_uv_masks = []

    @abc.abstractmethod
    def initialize(self):
        """Initialize server."""

    def ciphertext_accumulate(self, data, client_id):
        """Accumulate client's data, the data is ciphertext."""

    @abc.abstractmethod
    async def decrypt(self):
        """Decrypt the accumulated data."""

    @abc.abstractmethod
    def handle_msg(self, msg):
        """Process the ssa protocol message."""

    def _accumulate_data(self, data):
        if isinstance(data, list):
            # tf's weights is a list/numpy.ndarray
            self._accumulate_list(data)
        elif isinstance(data, OrderedDict):
            # pytorch's weights is a OrderedDict
            self._accumulate_ordereddict(data)
        elif can_be_added(data):
            self._total_data = np.add(self._total_data, data)
        else:
            raise TypeError('Not support data type %s' % type(data))

    def _accumulate_list(self, data):
        if not self._total_data:
            self._total_data = data
            return

        for index, value in enumerate(data):
            self._total_data[index] = np.add(
                self._total_data[index], value)

    def _accumulate_ordereddict(self, data):
        if not self._total_data:
            self._total_data = data
            return
        for name, value in data.items():
            self._total_data[name] = np.add(
                self._total_data.get(name, 0), value)


class SSAServer(SSABaseServer):
    """Secret Share Aggregate, used to generate mask and decrypt data.

    Args:
        handle: The unique string represents this encryption and decryption.
        min_client_num: Minimum number of clients required.
        client_num: Number of participating clients.
        use_same_mask: Whether to use the same mask. True mean all weights
            use a ame mask, False mean use different mask in different
            layers in weights.
        wait_aggregate_interval: the time to wait for use descrypt.
        ssl_key: the ssl path to use GRPCS.
        kwargs:
            stage_time_interval: the time to wait a stage timeout.
    """
    def __init__(self, handle, min_client_num, client_num, use_same_mask,
                 wait_aggregate_interval,
                 ssl_key=None, **kwargs):
        super().__init__(handle, min_client_num, client_num, use_same_mask,
                         ssl_key)

        self.__stage_time_interval = kwargs.get("stage_time_interval",
                                                STAGE_TIME_INTERVAL)
        self.__wait_aggregate_interval = wait_aggregate_interval
        self.__wait_aggregate_timer = None

        self.__initialize_finished_event = asyncio.Event()
        self.__mask_ready_event = asyncio.Event()

        self.__rpt_public_key_num = 0
        self.__rpt_encrypted_share_clients = []
        self.__rpt_masked_result_clients = []
        self.__rpt_secret_share_num = 0

        self.__public_keys = {}
        self.__encrypted_shares = {}
        self.__secret_shares = []

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

    def __set_initialize_finished_ready(self):
        self.__initialize_finished_event.set()

    async def __wait_initialize_finished_ready(self):
        await self.__initialize_finished_event.wait()

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
            self.__set_initialize_finished_ready()
            self.__clear()

    def __handle_public_key(self, msg):
        self.__assert_stage(ProtocolStage.ExchangePublicKey)

        self.__save_public_key(msg.public_key_rpt)
        self.__rpt_public_key_num += 1

        if self.__rpt_public_key_num == self._client_num:
            self.__exchange_public_keys()

    def __save_public_key(self, public_key):
        self.__public_keys[public_key.client_id] = public_key

    def __exchange_public_keys(self):
        try:
            self.__stop_stage_timer()
            self.__stage = ProtocolStage.ExchangeEncryptedShare

            msg = self.__encode_public_keys_msg()
            self.__broadcast_pks_to_clients(
                self.__public_keys, msg)

            self.__start_stage_timer(self.__exchange_encrypted_shares)
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

    def __broadcast_pks_to_clients(self, client_list, msg):
        for alive_client_id in client_list:
            asyncio.create_task(
                self.__send_pks(alive_client_id, msg))

    async def __send_pks(self, client_id, msg):
        await unary_call(SSAServiceStub, 'call', msg,
                         client_id,
                         certificate_path=self._ssl_key,
                         metadata={"destination": client_id})

    def __handle_encrypted_shares(self, msg):
        self.__assert_stage(ProtocolStage.ExchangeEncryptedShare)

        self.__save_encrypted_shares(msg.encrypted_shares_rpt)
        self.__rpt_encrypted_share_clients.append(
            msg.encrypted_shares_rpt.client_id)

        if (len(self.__rpt_encrypted_share_clients)
                == self.__rpt_public_key_num):
            self.__exchange_encrypted_shares()

    def __save_encrypted_shares(self, encrypted_shares):
        self.__encrypted_shares[encrypted_shares.client_id] = encrypted_shares

    def __exchange_encrypted_shares(self):
        try:
            self.__stop_stage_timer()
            self.__stage = ProtocolStage.CiphertextAggregate

            new_encrypted_shares = self.__reconstruct_encrypted_shares()
            self.__broadcast_encrypted_shares(
                new_encrypted_shares)

            self.__set_initialize_finished_ready()
        except Exception as err:
            logging.exception(str(err))
            self.__process_error(str(err))

    def __reconstruct_encrypted_shares(self):
        """
        old encrypted_shares   first loop    new_encrypted_shares
        1: [ null,   (1,2,a), (1,3,b)],   1: [()]         1:[(2,1,c), (3,1,e)]
        2: [(2,1,c), null,    (2,3,d)],-> 2: [(2,1,a)]->  2:[(1,2,a), (3,2,f)]
        3: [(3,1,e), (3,2,f), null ]      3: [(3,1,b)]    3:[(1,3,b), (2,3,d)]
        """
        new_encrypted_shares = {}

        for client_id_u, encrypted_shares in self.__encrypted_shares.items():
            for encrypted_share in encrypted_shares.encrypted_share:
                client_id_v = encrypted_share.client_id
                if client_id_u == client_id_v:
                    continue

                new_encrypted_share = EncryptedShare(client_id=client_id_u,
                                                     data=encrypted_share.data)
                try:
                    new_encrypted_shares[client_id_v].encrypted_share.append(
                        new_encrypted_share)
                except KeyError:
                    new_encrypted_shares[client_id_v] = \
                        EncryptedShares()
                    new_encrypted_shares[client_id_v].encrypted_share.append(
                        new_encrypted_share)

        return new_encrypted_shares

    def __encode_encrypted_shares_msg(self, encrypted_shares):
        return SSAMessage(
            handle=self._handle,
            encrypted_shares_bcst=encrypted_shares)

    def __broadcast_encrypted_shares(self, encrypted_shares_s):
        for client_id in self.__encrypted_shares:
            msg = self.__encode_encrypted_shares_msg(
                encrypted_shares_s[client_id])
            asyncio.create_task(self.__send_encrypted_shares(client_id, msg))

    async def __send_encrypted_shares(self, client_id, msg):
        await unary_call(SSAServiceStub, 'call', msg,
                         client_id,
                         certificate_path=self._ssl_key,
                         metadata={"destination": client_id})

    def ciphertext_accumulate(self, data, client_id):
        """Accumulate client's data, the data is ciphertext.

        Args:
            data: The data reported by client, which will be aggregated.
            client_id: which client report the data.
        """
        if self.__stage in (None, ProtocolStage.ExchangePublicKey,
                            ProtocolStage.ExchangeEncryptedShare):
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
        await self.__wait_initialize_finished_ready()
        self.__assert_stage(ProtocolStage.CiphertextAggregate)
        self.__stop_wait_aggregate_timer()
        self.__raise_exception_if_error()

        self.__stage = ProtocolStage.DecryptResult
        self.__start_stage_timer(self.__generate_double_mask)

        self.__broadcast_alive_clients()

        await self.__wait_mask_ready()
        self.__raise_exception_if_error()

        return self.__do_decrypt()

    def __broadcast_alive_clients(self):
        msg = self.__encode_alive_clients_msg()
        for alive_client_id in self.__rpt_masked_result_clients:
            asyncio.create_task(
                self.__send_alive_clients(alive_client_id, msg))

    async def __send_alive_clients(self, client_id, msg):
        await unary_call(SSAServiceStub, 'call', msg,
                         client_id,
                         certificate_path=self._ssl_key,
                         metadata={"destination": client_id})

    def __encode_alive_clients_msg(self):
        clients = Clients()
        for client_id in self.__rpt_masked_result_clients:
            clients.client_id.append(client_id)

        return SSAMessage(
            handle=self._handle,
            alive_clients_bcst=clients)

    async def __wait_mask_ready(self):
        await self.__mask_ready_event.wait()

    def __do_decrypt(self):
        if isinstance(self._total_data, list):
            self.__decrypt_list()
        elif isinstance(self._total_data, OrderedDict):
            self.__decrypt_ordered_dict()
        elif can_be_added(self._total_data):
            masks = self._genernate_masks(1)
            self._total_data = np.add(
                self._total_data, masks[0])
        else:
            raise TypeError('Not support data type %s' %
                            type(self._total_data))
        return self._total_data

    def __decrypt_list(self):
        if not self._use_same_mask:
            masks = self._genernate_masks(len(self._total_data))
            for index, value in enumerate(self._total_data):
                self._total_data[index] = np.add(value, masks[index])
        else:
            masks = self._genernate_masks(1)
            for index, value in enumerate(self._total_data):
                self._total_data[index] = np.add(value, masks[0])

    def __decrypt_ordered_dict(self):
        if not self._use_same_mask:
            masks = self._genernate_masks(len(self._total_data))
            for index, (name, value) in enumerate(self._total_data.items()):
                self._total_data[name] = np.add(value, masks[index])
        else:
            masks = self._genernate_masks(1)
            for name, value in self._total_data.items():
                self._total_data[name] = np.add(value, masks[0])

    def _genernate_masks(self, data_size):
        masks = []
        for _ in range(data_size):
            b_total = 0
            for b_prg in self._b_masks:
                b_total += b_prg.next_number()

            s_total = 0
            for (drop_id, alive_id, s_uv_prg) in self._s_uv_masks:
                if drop_id > alive_id:
                    s_total += s_uv_prg.next_number()
                else:
                    s_total -= s_uv_prg.next_number()

            masks.append(s_total - b_total)
        logging.debug('masks %s', masks)
        return masks

    def __handle_secret_shares(self, msg):
        self.__assert_stage(ProtocolStage.DecryptResult)

        self.__save_secret_shares(msg.secret_shares_rpt)
        self.__rpt_secret_share_num += 1

        if self.__rpt_secret_share_num == len(self.__rpt_masked_result_clients):
            self.__generate_double_mask()

    def __save_secret_shares(self, secret_shares):
        self.__secret_shares.append(secret_shares)

    def __generate_double_mask(self):
        try:
            self.__stop_stage_timer()
            self.__assert_secret_shares()
            # to put the shares of the same client in one list.
            all_s_shares, all_b_shares = self.__reconstruct_secret_shares()

            self.__generate_s_uv_masks(all_s_shares)
            self.__generate_b_masks(all_b_shares)

        except Exception as err:
            logging.exception(str(err))
            self.__error = str(err)
        finally:
            self.__mask_ready_event.set()
            self.__clear()

    def __assert_secret_shares(self):
        if self.__secret_shares == []:
            raise RuntimeError("Has not enough surviving clients.")

    def __reconstruct_secret_shares(self):
        all_s_shares = {}
        all_b_shares = {}
        for secret_shares in self.__secret_shares:
            for b_share in secret_shares.b_share:
                try:
                    all_b_shares[b_share.client_id].append(b_share.data)
                except KeyError:
                    all_b_shares[b_share.client_id] = [b_share.data]
            for s_share in secret_shares.s_sk_share:
                try:
                    all_s_shares[s_share.client_id].append(s_share.data)
                except KeyError:
                    all_s_shares[s_share.client_id] = [s_share.data]

        return all_s_shares, all_b_shares

    def __generate_s_uv_masks(self, all_s_shares):
        drop_clients = set(self.__rpt_encrypted_share_clients)\
            - set(self.__rpt_masked_result_clients)
        s_sk_s = {}
        for client_id in drop_clients:
            if len(all_s_shares[client_id]) < self._min_client_num:
                raise RuntimeError(
                    "The number of s_sk shares report by client is less than "
                    "threshold, %s/%s." % (len(all_s_shares[client_id]),
                                           self._min_client_num))
            s_sk_s[client_id] = int(SecretSharer.recover_secret(
                all_s_shares[client_id]))

        diffie_hellman = DiffieHellman()
        for alive_client_id in self.__rpt_masked_result_clients:
            for drop_client_id in drop_clients:
                s_uv = diffie_hellman.agree(
                    s_sk_s[drop_client_id],
                    int(self.__public_keys[alive_client_id].s_pk))
                self._s_uv_masks.append((drop_client_id,
                                         alive_client_id,
                                         PseudorandomGenerator(s_uv)))

    def __generate_b_masks(self, all_b_shares):
        for client_id in self.__rpt_masked_result_clients:
            if len(all_b_shares[client_id]) < self._min_client_num:
                raise RuntimeError(
                    "The number of b shares report by client is less than "
                    "threshold, %s/%s." % (len(all_b_shares[client_id]),
                                           self._min_client_num))
            b_mask = int(SecretSharer.recover_secret(all_b_shares[client_id]))
            self._b_masks.append(PseudorandomGenerator(b_mask))

    def __assert_stage(self, stage):
        if self.__stage is not stage:
            raise RuntimeError("The message has timed out and the "
                               "stage is now in %s." % self.__stage)

    def __raise_exception_if_error(self):
        if self.__error:
            raise RuntimeError(self.__error)

    def handle_msg(self, msg):
        """Process the ssa protocol message.
        """
        msg_handlers = {
            'public_key_rpt': self.__handle_public_key,
            'encrypted_shares_rpt': self.__handle_encrypted_shares,
            'secret_shares_rpt': self.__handle_secret_shares
        }

        which = msg.WhichOneof('spec')
        msg_handlers[which](msg)
