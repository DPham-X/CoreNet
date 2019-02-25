import logging
import yaml
from jnpr.junos import Device
from jnpr.junos.exception import ConnectError
from datetime import datetime

logger = logging.getLogger(__name__)


class BackupTrigger(object):
    def __init__(self, backup_folder='backups/', config_path='config/devices.yaml'):
        self.backup_folder = backup_folder
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

    def backup_config(self, args, uuid):
        command = 'show configuration | no-more'
        dev = self.connected_devices[args]
        logger.info('Executing CLI command: %s', command)
        output = dev.cli(command)
        date = datetime.now().isoformat().replace(':','_')
        filename = '{}config_{}_{}.conf'.format(self.backup_folder, date, uuid)
        with open(filename, 'w') as f:
            f.write(output)
        return 'Config was backed up to {}'.format(filename)

    def execute(self, vars, uuid):
        command  = vars['cmd']
        args = vars['args']

        if 'backup.config' == command:
            output = self.backup_config(args, uuid)
        else:
            logger.error('Undefined BackupTrigger command ... skipping - %s', command)
            return False
        return output