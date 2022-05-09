#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=not-callable
"""Authentication module.
"""
from absl import logging

from OpenSSL import crypto

from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import MD5


class Authenticator:
    """Authenticate clients.
    """

    def __init__(self, root_certs):
        self.__public_keys = {}
        self.__root_cert = None
        self.__root_store = None

        self.__load_root_cert(root_certs)

    def __load_root_cert(self, path):
        if not path:
            self.__root_cert = None
            logging.warning("No root cert config.")
            return

        cert = open(path, "rb").read()
        self.__root_cert = crypto.load_certificate(crypto.FILETYPE_PEM, cert)
        self.__root_store = crypto.X509Store()
        self.__root_store.add_cert(self.__root_cert)

    def authenticate(self, auth_info):
        """Authenticate the client.

        Authentication client in this function, only pass the authentication can
        join the federate learning. And when pass the authentication, add the
        client public key.
        {
            "client_id": "oiu",
            "certificate": ".....",
            "username": "test",
            "password": "***",  # can be base64
            "public_key": "...."
        }

        Args:
            auth_info: certification information. it can use account(username
            and password) or certificate.
        """
        if auth_info.certificate:
            pub_key = self.__auth_certificate(auth_info.certificate)
        else:
            self.__auth_account(auth_info.username, auth_info.password)
            pub_key = auth_info.public_key

        if not pub_key:
            raise Exception("Client %s Authenticate failed." %
                            auth_info.client_id)

        self.__public_keys[auth_info.client_id] = pub_key

    def __auth_account(self, username, password):
        """Auth client with username and password.

        This way apply to cross-device, user send it's account info to auth. And
        upload it's public key for signature verification.
        TODO This should authenticate to user management.
        """
        del password
        logging.info("Auth username and password.")
        if username == "test":  # TODO delete after test.
            return True
        raise NotImplementedError("User %s authenticate failed." % username)

    def __auth_certificate(self, certificate):
        """Auth the client's certificate.

        This way is more apply to cross-silo, the certificate should be
        authenticated before.
            1. This certificate can be certified by a third-party certificate
            authority.
            2. This certificate also can be a certificate issued by the server's
            own root certificate.

        Then parse the public key from certificate.
        """
        logging.info("Auth client certificate.")
        if not self.__root_cert:
            raise Exception("Verify certificate failed, no root cert.")
        client_cert = crypto.load_certificate(crypto.FILETYPE_PEM, certificate)
        store_ctx = crypto.X509StoreContext(self.__root_store, client_cert)
        # Verify the certificate, returns None if it can validate success.
        try:
            store_ctx.verify_certificate()
            return client_cert.get_pubkey()
        except crypto.X509StoreContextError as err:
            logging.info("Verify certificate failed, %s", str(err))
            return None

    def verify(self, client_info, signature):
        """Client Signature Verification.

        Verify the client info is from the legal registered client and the
        message not be tampered.
        """
        logging.info("Verify client %s signature.", client_info.client.id)
        if client_info.client.id not in self.__public_keys:
            raise Exception("Unauthorized Client %s" % client_info.client.id)

        message = client_info.SerializeToString()
        if isinstance(message, str):
            msg_h = MD5.new(message.encode('utf-8'))
        else:
            msg_h = MD5.new(message)

        client_public_key = self.__public_keys[client_info.client.id]
        rsa_public_key = RSA.importKey(client_public_key)
        verifier = PKCS1_v1_5.new(rsa_public_key)
        if verifier.verify(msg_h, signature):
            logging.info("Message match the signature, auth success.")
        else:
            raise Exception("Invalid Signature.")
