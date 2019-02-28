import logging
import warnings
import re

import cryptography
import yaml
from cryptography import utils
from jnpr.junos import Device
from jnpr.junos.exception import ConnectError
from jnpr.junos.utils.start_shell import StartShell
from .conn_device import ConnDevice

with warnings.catch_warnings():
    warnings.simplefilter('ignore', cryptography.utils)
    import cryptography.hazmat.primitives.constant_time

logger = logging.getLogger(__name__)


class JunosCliTrigger(ConnDevice):
    def __init__(self, config_path='config/devices.yaml', *args, **kwargs):
        logger.info('Started JunosCliTrigger')
        super(JunosCliTrigger, self).__init__(*args, **kwargs)

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