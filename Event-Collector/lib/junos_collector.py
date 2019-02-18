import json
import logging
import logging.config
import sys
import time
import uuid
from datetime import datetime

import requests
import yaml
from jnpr.junos import Device
from jnpr.junos.exception import ConnectError

logger = logging.getLogger(__name__)


class JunosCollector(object):
    def __init__(self, device_config):
        """ Junos RPC information collector """
        self.connected_devices = {}
        self.network_devices = {}
        self.db_url = 'http://localhost:5000/create_event'
        self._import_network_devices(device_config)
        self.start_monitoring()

    def start_monitoring(self):
        self.interface_status = {}

        while True:
            self.get_interface_status()
            self.interfaces_to_monitor()
            time.sleep(30)

    def add_event_to_db(self, event_msg):
        headers = {
            'Content-Type': 'application/json',
        }
        requests.post(self.db_url, json=event_msg, headers=headers)

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
        # TODO: wrap in error debugs
        try:
            logger.debug('Connecting to %s', device['ip'])
            dev = Device(host=device['ip'], user=device['user'], password=device['password']).open()
            logger.info('Successfully connected to %s', device['ip'])
        except ConnectError as e:
            logger.error('%s', str(e))
            raise ConnectError(e)
        else:
            self.connected_devices[device['name']] = dev

    def get_interface_status(self):
        device_interface_statuses = {}
        rpc_replies = {}
        for dev_name, connected_dev in self.connected_devices.items():
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

        self.interface_status = device_interface_statuses

    def interfaces_to_monitor(self):
        to_monitor = ['ge-0/0/1']
        for device_name, interfaces in self.interface_status.items():
            oper_status_down = []
            admin_status_down = []
            for interface_name, interface in interfaces.items():
                if interface_name not in to_monitor:
                    continue
                if interface['oper-status'] == 'down':
                    oper_status_down.append(interface_name)
                if interface['admin-status'] == 'down':
                    admin_status_down.append(interface_name)

            if oper_status_down:
                event = {
                    'uuid': str(uuid.uuid4()),
                    'time': str(datetime.now().isoformat()),
                    'name': 'Monitored oper interface is down',
                    'type': 'cli',
                    'priority': 'critical',
                    'body': {device_name: json.dumps(oper_status_down)},
                }
                self.add_event_to_db(event)
                logger.info('%s - %s - %s', event['uuid'], event['time'], event['name'])

            if admin_status_down:
                event = {
                    'uuid': str(uuid.uuid4()),
                    'time': str(datetime.now().isoformat()),
                    'name': 'Monitored admin interface is down',
                    'type': 'cli',
                    'priority': 'critical',
                    'body': {device_name: json.dumps(admin_status_down)},
                }
                self.add_event_to_db(event)
                logger.info('%s - %s - %s', event['uuid'], event['time'], event['name'])

if __name__ == '__main__':
    jc = JunosCollector(device_config='../config/devices.yaml')
