#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=too-few-public-methods
""" ssl helper

reference:
https://github.com/vmagamedov/grpclib/blob/master/examples/mtls/server.py
"""
import os
import ssl
import threading


class SSLConfigError(Exception):
    """SSL config not exist error
    """


class SSLContext:
    """SSLContext used for grpcs.
    """
    _instance_lock = threading.Lock()

    @classmethod
    def instance(cls, certificate_path):
        """Singleton instance, create SSLContext for grpcs.

        Args:
            certificate_path: where have the certificate,
            and must contain 3 files:
                - cert.pem: the certificate in.
                - private.key: the private key in.
                - trusted.pem: the trusted certificate in.
        """
        if not certificate_path:
            return None

        cert, key, trusted = _get_certificate_config_path(
            certificate_path)
        _check_file_exist(cert, key, trusted)
        return _create_secure_context(cert, key, trusted)


def _get_certificate_config_path(config_path):
    cert = os.path.join(config_path, 'cert.pem')
    key = os.path.join(config_path, 'private.key')
    trusted = os.path.join(config_path, 'trusted.pem')

    return cert, key, trusted


def _check_file_exist(*file_paths):
    for file_path in file_paths:
        if not os.path.exists(file_path):
            raise SSLConfigError('%s not exist, in ssl config path, must have'
                                 ' file: [cert.pem, private.key, trusted.pem]'
                                 % file_path)


def _create_secure_context(server_cert, server_key, trusted):
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS)
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.load_cert_chain(server_cert, server_key)
    ctx.load_verify_locations(trusted)
    ctx.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
    # set  encryption algorithm, from 'openssl ciphers -V'
    ctx.set_ciphers('ECDHE-RSA-AES256-GCM-SHA384:DH-DSS-AES128-GCM-SHA256')
    ctx.set_alpn_protocols(['h2'])
    try:
        ctx.set_npn_protocols(['h2'])
    except NotImplementedError:
        pass
    return ctx
