#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""AES encryption.
"""

import hashlib

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def encrypt_with_gcm(key, msg, number_once, associated_data):
    """Use GCM to encrypt.
    """
    nonce = hashlib.md5(number_once.encode()).digest()
    aesgcm = AESGCM(hashlib.md5(str(key).encode()).digest())
    return aesgcm.encrypt(nonce, msg.encode(), associated_data.encode())


def decrypt_with_gcm(key, ciphertext, number_once, associated_data):
    """Use GCM to decrypt.
    """
    nonce = hashlib.md5(number_once.encode()).digest()
    aesgcm = AESGCM(hashlib.md5(str(key).encode()).digest())
    return aesgcm.decrypt(nonce, ciphertext, associated_data.encode()).decode()
