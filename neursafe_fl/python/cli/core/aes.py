#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Use AES to encrypt and decrypt message"""

import base64

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


_KEY = b'\xb7\xa9[\x97\x9a\xa0M~\x1c\x84\xeeQ\x85}\x83S'
_NONCE = b':MkC\x17hn_\xb0\xae\xca\xf8'


def encrypt(msg):
    """Use GCM to encrypt.
    """
    aesgcm = AESGCM(_KEY)
    return bytes.decode(
        base64.encodebytes(
            aesgcm.encrypt(_NONCE, msg.encode(), None)))


def decrypt(ciphertext):
    """Use GCM to decrypt.
    """
    aesgcm = AESGCM(_KEY)
    return aesgcm.decrypt(
        _NONCE,
        base64.decodebytes(str.encode(ciphertext)),
        None).decode()
