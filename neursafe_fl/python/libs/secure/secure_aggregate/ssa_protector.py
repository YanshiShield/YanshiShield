#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=invalid-name, eval-used
"""
Protect data by SSA
"""
import os
import asyncio
import fcntl
import pickle

from collections import OrderedDict
from absl import logging

import numpy as np

from neursafe_fl.python.libs.secure.secure_aggregate.common import \
    PseudorandomGenerator, can_be_added
from neursafe_fl.python.libs.secure.secure_aggregate.aes import decrypt_with_gcm
from neursafe_fl.python.client.executor.errors import FLError

WAIT_INTERNAL = 1
WAIT_TIMEOUT = 3600


class SSAProtector:
    """Protect data according SSA algorithm
    """

    def __init__(self, secret_file_path, use_same_mask, timeout=WAIT_TIMEOUT):
        self.use_same_mask = use_same_mask
        self.secret_file_path = secret_file_path
        self.wait_timeout = timeout

        self.b = None
        self.s_uv_s = []
        self.id_ = None

    def _generate_masks(self, data_size):
        if self.b:
            b_prg = PseudorandomGenerator(self.b)
        else:
            b_prg = None

        masks = []
        for _ in range(data_size):
            s_total = 0
            for (v_id, s_uv_prg) in self.s_uv_s:
                if self.id_ > v_id:
                    s_total += s_uv_prg.next_number()
                else:
                    s_total -= s_uv_prg.next_number()

            if b_prg:
                masks.append(b_prg.next_number() + s_total)
            else:
                masks.append(s_total)
        logging.debug('masks %s', masks)
        return masks

    def __encrypt_list(self, data):
        new_data = []
        if not self.use_same_mask:
            masks = self._generate_masks(len(data))
            for index, item in enumerate(data):
                new_data.append(np.add(item, masks[index]))
        else:
            masks = self._generate_masks(1)
            for item in data:
                new_data.append(np.add(item, masks[0]))
        return new_data

    def __encrypt_ordered_dict(self, data):
        new_data = OrderedDict()
        if not self.use_same_mask:
            masks = self._generate_masks(len(data))
            for index, (name, value) in enumerate(data.items()):
                new_data[name] = np.add(value, masks[index])
        else:
            masks = self._generate_masks(1)
            for name, value in data.items():
                new_data[name] = np.add(value, masks[0])
        return new_data

    async def wait_ready(self):
        """
        Wait secret shares file saved successfully, because encrypt data
        depending on the file.
        """
        retry_times = 0
        while not os.path.exists(self.secret_file_path):
            retry_times += 1
            if retry_times > self.wait_timeout:
                raise FLError("Wait secret file ready timeout.")

            await asyncio.sleep(WAIT_INTERNAL)

        with open(self.secret_file_path, "rb") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            encrypted_info = pickle.load(f)

        secret_info = pickle.loads(eval(
            decrypt_with_gcm(self.secret_file_path, encrypted_info,
                             self.secret_file_path, self.secret_file_path)))

        self.b = secret_info["b"]
        self.s_uv_s = secret_info["s_uv_s"]
        self.id_ = secret_info["id"]

        if os.path.exists(self.secret_file_path):
            os.remove(self.secret_file_path)

    def encrypt(self, data):
        """Encrypt data

        Args:
            data: data which need to be protect
        """
        if isinstance(data, list):
            # tf's weights is list, the value is ndarray
            new_data = self.__encrypt_list(data)
        elif isinstance(data, OrderedDict):
            # pytorch's value in OrderedDict, the value is torch.Tensor
            new_data = self.__encrypt_ordered_dict(data)
        elif can_be_added(data):
            masks = self._generate_masks(1)
            new_data = np.add(data, masks[0])
        else:
            raise TypeError('Not support data type %s' % type(data))

        return new_data
