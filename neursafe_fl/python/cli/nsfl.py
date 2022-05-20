#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Main of nsfl command.
"""

import os

import click

from neursafe_fl.python.cli.core.context import PASS_CONTEXT, set_log


class ComplexCLI(click.MultiCommand):
    """Subcommands of nsfl"""
    def list_commands(self, ctx):
        """List all commands."""
        subcmds = []
        cmd_folder = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                  'commands'))
        for filename in os.listdir(cmd_folder):
            if filename.endswith('.py') and filename.startswith('cmd_'):
                subcmds.append(filename[4:-3])
        subcmds.sort()
        return subcmds

    def get_command(self, _, cmd_name):
        """Get command for command name."""
        try:
            mod = __import__('neursafe_fl.python.cli.commands.cmd_' + cmd_name,
                             None, None, ['cli'])
        except ImportError:
            return None
        return mod.cli


@click.command(cls=ComplexCLI)
@click.option('-d', '--debug', is_flag=True, help='Set nsfl in debug model.')
@PASS_CONTEXT
def nsfl(_, debug):
    """
    nsfl is CLI client for Federate Learning Platform. You should use
    'nsfl set config -s ip:port -d data_server -u user -p' to set the address
    of aip server and other config. Next, you could use 'nsfl health' to check
    server runing ok. Then you can use nsfl other subcommand to run job for
    federated learning.
    """
    set_log(debug)


if __name__ == "__main__":
    nsfl()  # pylint:disable=no-value-for-parameter
