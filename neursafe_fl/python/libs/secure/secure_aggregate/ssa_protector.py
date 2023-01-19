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

import numpy as np

from neursafe_fl.python.libs.secure.secure_aggregate.common import \
    PseudorandomGenerator, can_be_added, get_shape
from neursafe_fl.python.libs.secure.secure_aggregate.aes import decrypt_with_gcm
from neursafe_fl.python.libs.secure.secure_aggregate.common import \
    PLAINTEXT_MULTIPLE
from neursafe_fl.python.client.executor.errors import FLError

WAIT_INTERNAL = 1
WAIT_TIMEOUT = 3600


class SSAProtector:
    """Protect data according SSA algorithm
    """

    def __init__(self, secret_file_path, timeout=WAIT_TIMEOUT):
        self.secret_file_path = secret_file_path
        self.wait_timeout = timeout

        self.b = None
        self.s_uv_s = []
        self.id_ = None

    def __generate_mask(self, shape, b_prg=None):
        mask = np.zeros(shape)
        for (v_id, s_uv_prg) in self.s_uv_s:
            if self.id_ > v_id:
                mask = np.add(mask, s_uv_prg.next_value(shape))
            else:
                mask = np.subtract(mask, s_uv_prg.next_value(shape))

        if b_prg:
            mask = np.add(mask, b_prg.next_value(shape))

        return mask if shape != (1,) else mask[0]

    def __gen_b_prg(self):
        if self.b:
            return PseudorandomGenerator(self.b)

        return None

    def __encrypt_list(self, data):
        new_data = []

        b_prg = self.__gen_b_prg()

        for item in data:
            shape = get_shape(item)
            mask = self.__generate_mask(shape, b_prg)
            new_data.append(item * PLAINTEXT_MULTIPLE + mask)

        return new_data

    def __encrypt_ordered_dict(self, data):
        new_data = OrderedDict()

        b_prg = self.__gen_b_prg()

        for name, value in data.items():
            shape = get_shape(value)
            mask = self.__generate_mask(shape, b_prg)
            new_data[name] = np.add(value * PLAINTEXT_MULTIPLE, mask)

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
            shape = get_shape(data)
            b_prg = self.__gen_b_prg()
            mask = self.__generate_mask(shape, b_prg)
            new_data = np.add(data * PLAINTEXT_MULTIPLE, mask)
        else:
            raise TypeError('Not support data type %s' % type(data))

        return new_data
