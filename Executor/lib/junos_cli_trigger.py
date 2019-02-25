import logging
import warnings
import re

import cryptography
import yaml
from cryptography import utils
from jnpr.junos import Device
from jnpr.junos.exception import ConnectError
from jnpr.junos.utils.start_shell import StartShell

with warnings.catch_warnings():
    warnings.simplefilter('ignore', cryptography.utils)
    import cryptography.hazmat.primitives.constant_time

logger = logging.getLogger(__name__)


class JunosCliTrigger(object):
    def __init__(self, config_path='config/devices.yaml'):
        self.network_devices = {}
        self.connected_devices = {}

        self._import_network_devices(config_path)

    def _import_network_devices(self, network_device_file):
        logger.debug('Loading network devices into JunosCollector')
        with open(network_device_file, 'r') as f:
            import_devices = yaml.load(f.read())

        for device in import_devices['devices']:
            self.network_devices[device['name']] = device
            logger.debug('Imported credentials for %s', device['name'])

        for _, device in self.network_devices.items():
            self._connect_to_device(device)

    def _connect_to_device(self, device):
        try:
            logger.debug('Connecting to %s', device['ip'])
            dev = Device(host=device['ip'], user=device['user'], password=device['password']).open()
            logger.info('Successfully connected to %s', device['ip'])
        except ConnectError as e:
            logger.error('%s', str(e))
            raise ConnectError(e)
        else:
            self.connected_devices[device['name']] = dev

    def execute(self, vars):
        command = vars['cmd']
        args = vars['args']

        dev = self.connected_devices[args]
        logger.info('Executing CLI command: %s', command)

        with StartShell(dev) as ss:
            _, output = ss.run(r'cli -c "{} | no-more"'.format(command), timeout=30)
        if output:
            logger.info('Success')
            output = re.sub('\\r\\n---\(more\s\d+%\)---\\r\s+\r', '\n', output)
            output = output.replace('\r', '')
        return output

if __name__ == '__main__':
    jc = JunosCliTrigger('../config/devices.yaml')
    output = jc.execute({
        'cmd': 'show log messages | match interface | last 100',
        'args': 'P1'
    })
    print(repr(output))