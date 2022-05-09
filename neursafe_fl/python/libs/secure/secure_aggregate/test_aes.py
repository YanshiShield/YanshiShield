#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=missing-function-docstring
"""UnitTest of AES.
"""
import unittest

from neursafe_fl.python.libs.secure.secure_aggregate.aes import encrypt_with_gcm, \
    decrypt_with_gcm
from neursafe_fl.python.libs.secure.secure_aggregate.dh import DiffieHellman


class TestAES(unittest.TestCase):
    """Test class of AES.
    """

    def test_should_success_encrypt_and_decrypt(self):
        diffe_hellman = DiffieHellman()
        private1, _ = diffe_hellman.generate()
        _, public2 = diffe_hellman.generate()
        aes_key = diffe_hellman.agree(private1, public2)
        msg = 'my secret message'
        handle = 'test1-9'

        ciphertext = encrypt_with_gcm(aes_key, msg, handle, 'something')
        plaintext = decrypt_with_gcm(aes_key, ciphertext, handle, 'something')

        self.assertEqual(msg, plaintext)


if __name__ == "__main__":
    unittest.main()
