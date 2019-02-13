import logging
import logging.config
import sys
import time
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime

import yaml
from jnpr.junos import Device
from jnpr.junos.exception import ConnectError


logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
})
logger = logging.getLogger(__name__)


class JunosCollector(object):
    def __init__(self, device_config):
        self.connected_devices = {}
        self.network_devices = {}

        self._import_network_devices(device_config)

    def start_monitoring(self):
        self.interface_status = {}

        while True:
            self.get_interface_status()
            time.sleep(30)

    def _import_network_devices(self, network_device_file):
        logger.debug('Loading network devices into JunosCollector')
        with open(network_device_file, 'r') as file:
            import_devices = yaml.load(file.read())

        for device in import_devices['devices']:
            self.network_devices[device['name']] = device
            logger.debug('Imported credentials for {}'.format(device['name']))

        for _, device in self.network_devices.items():
            self._connect_to_device(device)

    def _connect_to_device(self, device):
        dev = Device(host=device['ip'], user=device['user'], password=device['password'])
        self.connected_devices[device['name']] = dev

    def _get_device(self, hostname):
        try:
            logger.debug('Connecting to {}'.format(hostname))
            dev = self.connected_devices[hostname].open()
            logger.debug('Successfully connected to {}'.format(hostname))
        except ConnectError as e:
            logger.error(e)
            return
        return dev

    def get_interface_status(self):
        device_interface_statuses = {}
        rpc_replies = {}
        for dev_name in self.connected_devices:
            connected_dev = self._get_device(dev_name)
            if connected_dev is None:
                return

            rpc_reply = connected_dev.rpc.get_interface_information(terse=True)
            rpc_replies[dev_name] = rpc_reply

        for dev_name, rpc_reply in rpc_replies.items():
            device_interface_statuses[dev_name] = []
            interface_status = {}
            logical_interfaces = rpc_reply.xpath('//physical-interface|//logical-interface')

            for logical_interface in logical_interfaces:
                name = logical_interface.xpath('.//name')[0].text.replace('\n', '')
                admin_status = logical_interface.xpath('.//admin-status')[0].text.replace('\n', '')
                oper_status = logical_interface.xpath('.//oper-status')[0].text.replace('\n', '')
                interface_status[name] = {
                    'admin-status': admin_status,
                    'oper-status': oper_status,
                }
            device_interface_statuses[dev_name] = interface_status

        self.interface_status = {
            'uuid': str(uuid.uuid4()),
            'time': str(datetime.now()),
            'status': device_interface_statuses,
        }

if __name__ == '__main__':
    jc = JunosCollector(device_config='config/devices.yaml')
    jc.start_monitoring()