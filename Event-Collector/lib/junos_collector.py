import json
import logging
import logging.config
import sys
import time
import uuid
from datetime import datetime
from pprint import pprint

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
        self.db_url = 'http://10.49.227.135:5000/create_event'
        self._import_network_devices(device_config)
        self.start_monitoring()

    def start_monitoring(self):
        while True:
            # # Interface Status
            # device_interface_statuses = self.get_interface_status()
            # self.monitor_oper_status(device_interface_statuses)
            # self.monitor_admin_status(device_interface_statuses)

            # # BGP Peers
            # bgp_down_count = self.get_bgp_peers()
            # self.monitor_bgp_peers(bgp_down_count)

            # # LDP Neighbors
            # ldp_neighbors = self.get_ldp_session()
            # self.monitor_ldp_session(ldp_neighbors)

            # OSPF Neighbors
            ospf_neighbors = self.get_ospf_neighbors()
            self.monitor_ospf_neighbors(ospf_neighbors)
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
        try:
            logger.debug('Connecting to %s', device['ip'])
            dev = Device(host=device['ip'], user=device['user'], password=device['password']).open()
            logger.info('Successfully connected to %s', device['ip'])
        except ConnectError as e:
            logger.error('%s', str(e))
            raise ConnectError(e)
        else:
            self.connected_devices[device['name']] = dev

    def _create_event(self, name, type, priority, body):
        event = {
            'uuid': str(uuid.uuid4()),
            'time': str(datetime.now().isoformat()),
            'name': name,
            'type': type,
            'priority': priority,
            'body': json.dumps(body),
        }
        return event

    def get_interface_status(self):
        device_interface_statuses = {}
        rpc_replies = {}
        to_monitor = ['ge-0/0/0', 'ge-0/0/1', 'ge-0/0/2', 'ge-0/0/0.0', 'ge-0/0/1.0', 'ge-0/0/2.0']
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
                if name not in to_monitor:
                    continue
                admin_status = logical_interface.xpath('.//admin-status')[0].text.replace('\n', '')
                oper_status = logical_interface.xpath('.//oper-status')[0].text.replace('\n', '')
                interface_status[name] = {
                    'admin-status': admin_status,
                    'oper-status': oper_status,
                }
            device_interface_statuses[dev_name] = interface_status

        # self.interface_status = device_interface_statuses
        return device_interface_statuses

    def get_bgp_peers(self):
        device_bgp_peer_count = {}
        rpc_replies = {}
        to_monitor = ['P1', 'P2', 'P3']
        for dev_name, connected_dev in self.connected_devices.items():
            if connected_dev is None:
                return
            if dev_name not in to_monitor:
                continue

            rpc_reply = connected_dev.rpc.get_bgp_summary_information()
            rpc_replies[dev_name] = rpc_reply

        for dev_name, rpc_reply in rpc_replies.items():
            device_bgp_peer_count[dev_name] = {}
            device_bgp_peer_count[dev_name]['peer-count'] = 0
            device_bgp_peer_count[dev_name]['down-peer-count'] = 0

            try:
                peer_count_xpath = rpc_reply.xpath('//bgp-information/peer-count')
                down_peer_count_xpath = rpc_reply.xpath('//bgp-information/down-peer-count')

                if peer_count_xpath:
                    device_bgp_peer_count[dev_name]['peer-count'] = int(peer_count_xpath[0].text)
                if peer_count_xpath:
                    device_bgp_peer_count[dev_name]['down-peer-count'] = int(down_peer_count_xpath[0].text)
            except Exception as e:
                logger.error(e)

        return device_bgp_peer_count

    def get_ldp_session(self):
        ldp_neighbors = {}
        rpc_replies = {}
        to_monitor = ['P1', 'P2', 'P3', 'PE1', 'PE2', 'PE3', 'PE4']
        for dev_name, connected_dev in self.connected_devices.items():
            if connected_dev is None:
                return
            if dev_name not in to_monitor:
                continue

            rpc_reply = connected_dev.rpc.get_ldp_session_information()
            rpc_replies[dev_name] = rpc_reply

        for dev_name, rpc_reply in rpc_replies.items():
            ldp_neighbors[dev_name] = {}
            ldp_neighbors[dev_name]['ldp-session-state'] = ''
            ldp_neighbors[dev_name]['ldp-neighbor-address'] = ''
            try:
                ldp_session_xpath = rpc_reply.xpath('//ldp-session-information/ldp-session')

                for ldp_session in ldp_session_xpath:
                    ldp_neighbors[dev_name]['ldp-session-state'] = ldp_session.xpath('.//ldp-session-state')[0].text
                    ldp_neighbors[dev_name]['ldp-neighbor-address'] = ldp_session.xpath('.//ldp-neighbor-address')[0].text
            except Exception as e:
                logger.error(e)

        return ldp_neighbors

    def get_ospf_neighbors(self):
        o_ospf_neighbors = {}
        rpc_replies = {}
        to_monitor = ['P1', 'P2', 'P3', 'PE1', 'PE2', 'PE3', 'PE4']
        for dev_name, connected_dev in self.connected_devices.items():
            if connected_dev is None:
                return
            if dev_name not in to_monitor:
                continue

            rpc_reply = connected_dev.rpc.get_ospf_neighbor_information()
            rpc_replies[dev_name] = rpc_reply

        for dev_name, rpc_reply in rpc_replies.items():
            o_ospf_neighbors[dev_name] = {}
            o_ospf_neighbors[dev_name]['neighbor-address'] = ''
            o_ospf_neighbors[dev_name]['ospf-neighbor-state'] = ''
            o_ospf_neighbors[dev_name]['neighbor-id'] = ''
            o_ospf_neighbors[dev_name]['interface-name'] = ''
            try:
                ospf_neighbor_xpath = rpc_reply.xpath('//ospf-neighbor-information/ospf-neighbor')
                for ospf_neighbor in ospf_neighbor_xpath:
                    o_ospf_neighbors[dev_name]['neighbor-address'] = ospf_neighbor.xpath('.//neighbor-address')[0].text
                    o_ospf_neighbors[dev_name]['ospf-neighbor-state'] = ospf_neighbor.xpath('.//ospf-neighbor-state')[0].text
                    o_ospf_neighbors[dev_name]['neighbor-id'] = ospf_neighbor.xpath('.//neighbor-id')[0].text
                    o_ospf_neighbors[dev_name]['interface-name'] = ospf_neighbor.xpath('.//interface-name')[0].text
            except Exception as e:
                logger.error(e)
        return o_ospf_neighbors

    def monitor_oper_status(self, interface_status):
        for device_name, interfaces in interface_status.items():
            oper_status = []
            for interface_name, interface in interfaces.items():
                if interface['oper-status'] == 'down':
                    oper_status.append(interface_name)

            if oper_status:
                event = self._create_event(name='oper_status.interface.down.{}'.format(device_name),
                                           type='cli',
                                           priority='critical',
                                           body={device_name: oper_status})
                self.add_event_to_db(event)
                logger.info('%s - %s - %s', event['uuid'], event['time'], event['name'])
            else:
                event = self._create_event(name='oper_status.interface.up.{}'.format(device_name),
                                           type='cli',
                                           priority='information',
                                           body={device_name: oper_status})
                self.add_event_to_db(event)
                logger.info('%s - %s - %s', event['uuid'], event['time'], event['name'])

    def monitor_admin_status(self, interface_status):
        for device_name, interfaces in interface_status.items():
            admin_status = []
            for interface_name, interface in interfaces.items():
                if interface['admin-status'] == 'down':
                    admin_status.append(interface_name)

            if admin_status:
                event = self._create_event(name='admin_status.interface.down.{}'.format(device_name),
                                           type='cli',
                                           priority='critical',
                                           body={device_name: admin_status})
                self.add_event_to_db(event)
                logger.info('%s - %s - %s', event['uuid'], event['time'], event['name'])
            else:
                event = self._create_event(name='admin_status.interface.up.{}'.format(device_name),
                                           type='cli',
                                           priority='information',
                                           body={device_name: admin_status})
                self.add_event_to_db(event)
                logger.info('%s - %s - %s', event['uuid'], event['time'], event['name'])

    def monitor_bgp_peers(self, bgp_peer_count):
        for device_name, bgp_peer_count in bgp_peer_count.items():

            if bgp_peer_count['down-peer-count'] == 0:
                event = self._create_event(name='bgp.peers.up.{}'.format(device_name),
                            type='cli',
                            priority='information',
                            body={device_name: {
                                'up-peer-count': bgp_peer_count['peer-count'] - bgp_peer_count['down-peer-count'],
                                'down-peer-count': bgp_peer_count['down-peer-count'],
                            }})
                self.add_event_to_db(event)
                logger.info('%s - %s - %s', event['uuid'], event['time'], event['name'])
            else:
                event = self._create_event(name='bgp.peers.down.{}'.format(device_name),
                            type='cli',
                            priority='critical',
                            body={device_name: {
                                'up-peer-count': bgp_peer_count['peer-count'] - bgp_peer_count['down-peer-count'],
                                'down-peer-count': bgp_peer_count['down-peer-count'],
                            }})
                self.add_event_to_db(event)
                logger.info('%s - %s - %s', event['uuid'], event['time'], event['name'])

    def monitor_ldp_session(self, ldp_neighbors):
        for device_name, ldp_neighbor in ldp_neighbors.items():
            if ldp_neighbor['ldp-session-state'] == 'Operational':
                event = self._create_event(name='ldp.session.up.{}'.format(device_name),
                            type='cli',
                            priority='information',
                            body={device_name: ldp_neighbor})
                self.add_event_to_db(event)
                logger.info('%s - %s - %s', event['uuid'], event['time'], event['name'])
            else:
                event = self._create_event(name='ldp.session.down.{}'.format(device_name),
                            type='cli',
                            priority='critical',
                            body={device_name: ldp_neighbor})
                self.add_event_to_db(event)
                logger.info('%s - %s - %s', event['uuid'], event['time'], event['name'])

    def monitor_ospf_neighbors(self, ospf_neighbors):
        for device_name, ospf_neighbor in ospf_neighbors.items():
            if ospf_neighbor['ospf-neighbor-state'] == 'Full':
                event = self._create_event(name='ospf.neighbors.up.{}'.format(device_name),
                            type='cli',
                            priority='information',
                            body={device_name: ospf_neighbor})
                self.add_event_to_db(event)
                logger.info('%s - %s - %s', event['uuid'], event['time'], event['name'])
            else:
                event = self._create_event(name='ospf.neighbors.down.{}'.format(device_name),
                            type='cli',
                            priority='critical',
                            body={device_name: ospf_neighbor})
                self.add_event_to_db(event)
                logger.info('%s - %s - %s', event['uuid'], event['time'], event['name'])

if __name__ == '__main__':
    jc = JunosCollector(device_config='../config/devices.yaml')
