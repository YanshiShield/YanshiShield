#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Main of nsfl command.
"""

import os

import click

from neursafe_fl.python.cli.core.context import PASS_CONTEXT, set_log


VERSION = "0.1.0"


class ComplexCLI(click.MultiCommand):
    """List sub-commands of nsfl
    """

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


def print_version(ctx, param, value):
    """Print version of cli tool.
    """
    del param
    if not value or ctx.resilient_parsing:
        return
    click.echo('Version %s' % VERSION)
    ctx.exit()


@click.command(cls=ComplexCLI)
@click.option('-d', '--debug', is_flag=True, help='Set nsfl-ctl command in'
                                                  ' debug mode, which means'
                                                  ' output log level is DEBUG.')
@click.option('-v', '--version', is_flag=True, callback=print_version,
              expose_value=False, is_eager=True, help='Show version '
                                                      'information and quit')
@PASS_CONTEXT
def nsfl(_, debug):
    """
    nsfl-ctl is the command line tool for Neursafe-FL, which is an open
    federated learning platform. Github address: \n
      https://github.com/neursafe/federated-learning \n
    Firstly, you should use 'set' sub-command to configure address of your
    federated environment before using other commands. For example: \n

      'nsfl-ctl set config -s ip:port -d ip:port -u user -p' \n

    Secondly, you can use 'nsfl-ctl health' to check if the connection is OK.

    Finally, if connection is OK, then you can use other sub-commands to manage
    your federated learning jobs or models.

    Run 'nsfl-ctl COMMAND --help' for more information.
    """
    set_log(debug)


if __name__ == "__main__":
    nsfl()  # pylint:disable=no-value-for-parameter
