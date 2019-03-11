import logging
import re
import warnings

import cryptography
from jnpr.junos.utils.start_shell import StartShell

from .conn_device import ConnDevice

with warnings.catch_warnings():
    warnings.simplefilter('ignore', cryptography.utils)
    import cryptography.hazmat.primitives.constant_time

logger = logging.getLogger(__name__)


class JunosCliTrigger(ConnDevice):
    def __init__(self, config_path='config/devices.yaml', *args, **kwargs):
        """Junos CLI Trigger which executes CLI commands

        :param ConnDevice: Junos Interface which holds all the connections to the
                           Junos network devices
        :type ConnDevice: ConnDevice object
        :param config_path: Location of the credentials for each network device,
                            defaults to 'config/devices.yaml'
        :param config_path: str, optional
        """
        super(JunosCliTrigger, self).__init__(*args, **kwargs)
        logger.info('Started JunosCliTrigger')

    def run_junos_cli_cmd(self, command, args):
        """Executes a CLI command on the Junos network device and
        returns output

        :param command: Command to run on the CLI
        :type command: str
        :param args: Name of the network device
        :type args: str
        :return: Output of the command that was ran
        :rtype: str
        """
        dev = self.connected_devices[args]
        logger.info('Executing CLI command: %s', command)

        with StartShell(dev) as ss:
            _, output = ss.run(r'cli -c "{} | no-more"'.format(command), timeout=30)

        if output:
            output = re.sub(r'\r\n---\(more\s\d+%\)---\r\s+', '\n', output)
            output = output.replace('\r', '')
        return output

    def execute(self, vars):
        """Executes JunosCliTrigger valid commands

        :param vars: Has all information on the action to take including
                     the command to be run and arguments associated with it
        :type vars: dict
        :return: Output of the command that was executed
        :rtype: str
        """
        command = vars['cmd']
        args = vars['args']

        output = self.run_junos_cli_cmd(command, args)
        if not output:
            return '', False
        return output, True


if __name__ == '__main__':
    # Example
    jc = JunosCliTrigger('../config/devices.yaml')
    output = jc.execute({
        'cmd': 'show log messages | match interface | last 100',
        'args': 'P1'
    })
    print(repr(output))
