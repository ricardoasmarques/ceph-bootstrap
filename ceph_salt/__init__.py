import logging
import logging.config
import signal
import sys
import time

import click
import pkg_resources

from .config_shell import run_config_cmdline, run_config_shell, run_status, run_export, run_import
from .exceptions import CephSaltException
from .logging_utils import LoggingUtil
from .terminal_utils import check_root_privileges, PrettyPrinter as PP
from .execute import CephSaltExecutor


logger = logging.getLogger(__name__)


def ceph_salt_main():
    try:
        # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
        cli(prog_name='ceph-salt')
    except CephSaltException as ex:
        logger.exception(ex)
        PP.pl_red(str(ex))
        sys.exit(1)


@click.group()
@click.option('-l', '--log-level', default='info',
              type=click.Choice(["info", "error", "debug", "silent"]),
              help="set log level (default: info)")
@click.option('--log-file', default='/var/log/ceph-salt.log',
              type=click.Path(dir_okay=False),
              help="the file path for the log to be stored")
@click.version_option(pkg_resources.get_distribution('ceph-salt'), message="%(version)s")
@check_root_privileges
def cli(log_level, log_file):
    LoggingUtil.setup_logging(log_level, log_file)


@cli.command(name='config')
@click.argument('config_args', nargs=-1, type=click.UNPROCESSED, required=False)
def config_shell(config_args):
    """
    Start ceph-salt configuration shell
    """
    if config_args:
        def _quote(text):
            if ' ' in text:
                return '"{}"'.format(text)
            return text
        config_args = [_quote(config_arg) for config_arg in config_args]
        if not run_config_cmdline(" ".join(config_args)):
            sys.exit(1)
    else:
        if not run_config_shell():
            sys.exit(1)


@cli.command(name='status')
@click.option('-n', '--no-color', is_flag=True, default=False,
              help='Ouput without colors')
def status(no_color):
    """
    Check ceph-salt status
    """
    if no_color:
        PP.disable_colors()
    if not run_status():
        sys.exit(1)


@cli.command(name='export')
@click.option('-p', '--pretty', is_flag=True, default=False,
              help='Pretty-prints JSON ouput')
def export_config(pretty):
    """
    Export configuration
    """
    if not run_export(pretty):
        sys.exit(1)


@cli.command(name='import')
@click.argument('config_file', required=True)
def import_config(config_file):
    """
    Import configuration
    """
    if not run_import(config_file):
        sys.exit(1)


@cli.command(name='apply')
@click.option('-n', '--non-interactive', is_flag=True, default=False,
              help='Apply config in non-interactive mode')
@click.argument('minion_id', required=False)
def apply(non_interactive, minion_id):
    """
    Apply configuration by running ceph-salt formula
    """
    executor = CephSaltExecutor(not non_interactive, minion_id,
                                'ceph-salt', {})
    retcode = executor.run()
    sys.exit(retcode)


@cli.command(name='update')
@click.option('-n', '--non-interactive', is_flag=True, default=False,
              help='Update all packages')
@click.option('-r', '--reboot', is_flag=True, default=False,
              help='Reboot if needed')
@click.argument('minion_id', required=False)
def update(non_interactive, reboot, minion_id):
    """
    Update all packages
    """
    executor = CephSaltExecutor(not non_interactive, minion_id,
                                'ceph-salt.update', {
                                    'ceph-salt': {
                                        'updates': {
                                            'reboot': reboot
                                        }
                                    }
                                })
    retcode = executor.run()
    sys.exit(retcode)


if __name__ == '__main__':
    ceph_salt_main()
