#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Used to create ssa client and server."""

from neursafe_fl.python.libs.secure.secure_aggregate.ssa_client import SSAClient
from neursafe_fl.python.libs.secure.secure_aggregate.ssa_server import SSAServer
from neursafe_fl.python.libs.secure.secure_aggregate.ssa_simple_client import \
    SSASimpleClient
from neursafe_fl.python.libs.secure.secure_aggregate.ssa_simple_server import \
    SSASimpleServer


def create_ssa_client(mode, **kwargs):
    """Create ssa client."""
    client_map = {
        "doublemask": SSAClient,
        "onemask": SSASimpleClient,
    }
    return client_map[mode.lower()](**kwargs)


def create_ssa_server(mode, **kwargs):
    """Create ssa server."""
    server_map = {
        "doublemask": SSAServer,
        "onemask": SSASimpleServer,
    }
    return server_map[mode.lower()](**kwargs)
