import logging
import yaml
from jnpr.junos import Device
from jnpr.junos.exception import ConnectError
from datetime import datetime

# Logging
logger = logging.getLogger(__name__)


class ConnDevice(object):
    def __init__(self, config_path='config/devices.yaml'):
        """Common interface for connecting to Junos network devices.

        :param config_path: Location of the credentials for each network device
        :type config_path: str
        """
        self.network_devices = {}
        self.connected_devices = {}

        self._import_network_devices(config_path)

    def _import_network_devices(self, network_device_file):
        """Import the hostnames, username and password for each network device

        :param config_path: Location of the credentials for each network device
        :type config_path: str
        """
        logger.debug('Loading network devices into JunosCollector')
        with open(network_device_file, 'r') as f:
            import_devices = yaml.load(f.read())

        for device in import_devices['devices']:
            self.network_devices[device['name']] = device
            logger.debug('Imported credentials for %s', device['name'])

        for _, device in self.network_devices.items():
            self._connect_to_device(device)

    def _connect_to_device(self, device):
        """Connects to the network device via Netconf

        :param device: Contains the necessary information to connect to the device
        :type device: dict
        """
        try:
            logger.debug('Connecting to %s', device['ip'])
            dev = Device(host=device['ip'], user=device['user'], password=device['password']).open()
            logger.info('Successfully connected to %s', device['ip'])
        except ConnectError as e:
            logger.error('%s', str(e))
            raise ConnectError(e)
        else:
            self.connected_devices[device['name']] = dev