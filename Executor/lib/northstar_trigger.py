import json
import logging
import sys
from datetime import datetime, timedelta
import yaml
from time import sleep
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning


logger = logging.getLogger(__name__)

class NorthstarTrigger(object):
    access_token = None
    token_type = None
    base_url = None
    username = None
    password = None

    def __init__(self):
        """NorthStar REST API Translator"""
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        self._import_variables()

    def _import_variables(self):
        with open('config/auth.yaml') as file:
            imported_vars = yaml.load(file.read())

        self.base_url = 'https://{}:{}'.format(imported_vars['hostname'], imported_vars['port'])
        self.username = imported_vars['username']
        self.password = imported_vars['password']
        self.verify = False

    def _get_token(self):
        """Requests the Token needed for making NorthStar API calls

        Raises
        ------
        ConnectionError:
            When there is a problem in connecting to the Authentication API

        """
        payload = {'grant_type': 'password','username': self.username,'password': self.password}
        token_url = self.base_url + '/oauth2/token'
        logger.info('Connecting to {} with username: {}'.format(self.base_url, self.username))
        r = requests.post(token_url, data=payload, verify=self.verify ,auth=(self.username, self.password))

        try:
            assert r.status_code == 200
            reply = r.json()
            self.access_token = reply['access_token']
            self.token_type = reply['token_type']
            logger.debug('Got token: {}'.format(self.access_token))
            if self.access_token:
                logger.info('Authorization was successful')
        except IndexError as e:
            raise ConnectionError('Could not authenticate to NorthStar REST API: {}'.format(e))

    def _node_id_from_name(self, name, nodes):
        for node in nodes:
            if node['hostName'] == name:
                return node['nodeIndex']
        return None

    def get_topology_elements(self):
        """Retrieves a list of network nodes from the NorthStar API

        Raises
        ------
        ConnectionError:
            When there is a problem in connecting to the NorthStar API

        Returns
        -------
        : list
            List of nodes for each network device
        """
        self._get_token()
        topology_url = self.base_url + '/NorthStar/API/v2/tenant/1/topology/1/nodes'
        auth = '{} {}'.format(self.token_type, self.access_token)
        headers = {
            'Authorization': auth,
            'Content-Type': "application/json",
        }

        logger.debug('Getting topology elements')
        r = requests.get(topology_url, headers=headers, verify=self.verify)

        try:
            assert r.status_code == 200
            topology_information = r.json()
        except IndexError as e:
            raise ConnectionError('Could not get NorthStar topology elements')

        logger.debug('Received the following nodes:')
        logger.debug([node['hostName'] for node in topology_information])

        return topology_information

    def get_links(self):
        """Retrieves the link information for every link in the network

        Raises
        ------
        ConnectionError
            When there is a problem in connecting to the NorthStar API

        Returns
        -------
        : list
            List of NorthStar Links
        """
        self._get_token()
        links_url = self.base_url + '/NorthStar/API/v2/tenant/1/topology/1/links'
        auth = '{} {}'.format(self.token_type, self.access_token)
        headers = {
            'Authorization': auth,
            'Content-Type': "application/json",
        }

        logger.debug('Getting links')
        r = requests.get(links_url, headers=headers, verify=self.verify)

        try:
            assert r.status_code == 200
            link_information = r.json()
        except IndexError as e:
            raise ConnectionError('Could not get NorthStar links')

        logger.debug('Received the following links:')
        logger.debug([link['id'] for link in link_information])

        return link_information

    def create_new_maintenance(self, event_name, index):
        """Sets a device into maintenance given their index in the topology list

        Parameters
        ----------
        event_name : str
            Name of the maintenance event
        index : int
            Index of the network device as found in the network node list

        """
        self._get_token()
        maintenance_url = self.base_url + '/NorthStar/API/v2/tenant/1/topology/1/maintenances'
        auth = '{} {}'.format(self.token_type, self.access_token)
        start_time = datetime.now()
        end_time = datetime.now() + timedelta(days=7)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': auth,
        }
        body = {
            "topoObjectType": "maintenance",
            "topologyIndex": 1,
            "user": self.username,
            "name": event_name,
            "startTime": start_time.isoformat(),
            "endTime": end_time.isoformat(),
            "elements": [{"topoObjectType": "node", "index": index}]
        }
        existing_maintenances = self.get_maintenance_list()
        maintenances_name = [m['name'] for m in existing_maintenances]
        if event_name in maintenances_name:
            logger.info('Maintenance name already in use {}... skipping'.format(event_name))
            return

        logger.debug('Putting device into maintenance')
        logger.debug('Posting to: {}'.format(maintenance_url))
        r = requests.post(maintenance_url, json=body, headers=headers, verify=self.verify)
        assert r.status_code == 201, r.status_code
        logger.info('Successfully created maintenance event, Name:{} Start:{} End:{}'.format(event_name, start_time, end_time))

    def get_maintenance_list(self):
        self._get_token()
        maintenance_url = self.base_url + '/NorthStar/API/v2/tenant/1/topology/1/maintenances'
        auth = '{} {}'.format(self.token_type, self.access_token)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': auth,
        }

        logger.debug('Getting maintenance list')
        r = requests.get(maintenance_url, headers=headers, verify=self.verify)
        assert r.status_code == 200, r.status_code
        maintenance_list = r.json()
        logger.debug('Got the following maintenances')
        logger.debug([m['name'] for m in maintenance_list])
        return maintenance_list

    def update_maintenance(self, status, index, info):
        self._get_token()
        maintenance_url = self.base_url + '/NorthStar/API/v2/tenant/1/topology/1/maintenances/{}'.format(index)
        auth = '{} {}'.format(self.token_type, self.access_token)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': auth,
        }

        body = info
        if body['status'] != status:
            body['status'] = status
        else:
            logger.info('Maintenance status already in {}'.format(status))
            return

        r = requests.put(maintenance_url, json=body, headers=headers, verify=self.verify)
        logger.debug('Updating maintenance to {}'.format(status))
        assert r.status_code == 200, r.status_code

    def trigger_path_optimisation(self):
        self._get_token()
        path_optimisation_url = self.base_url + '/NorthStar/API/v2/tenant/1/topology/1/rpc/optimize'

        auth = '{} {}'.format(self.token_type, self.access_token)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': auth,
        }

        logger.debug('Triggering path optimisation')
        try:
            r = requests.request('POST', path_optimisation_url, data='', headers=headers, verify=self.verify)
            assert r.status_code == 200, r.status_code
        except AssertionError:
            return False
        response = r.json()
        logger.info(response['result '])

    def put_device_in_maintenance(self, router_name, event_name):
        topology_info = self.get_topology_elements()
        index = self._node_id_from_name(router_name, topology_info)
        logger.debug('Creating new maintenance for \'{}\''.format(router_name))
        self.create_new_maintenance(event_name, index)

    def delete_maintenance(self, event_name):
        maintenance_list = self.get_maintenance_list()
        maintenance_index = None
        maintenance_name = None

        for maintenance in maintenance_list:
            if event_name == maintenance['name']:
                maintenance_index = maintenance['maintenanceIndex']
                maintenance_info = maintenance
                maintenance_name = maintenance['name']

        if maintenance_name:
            self.update_maintenance('cancelled', maintenance_index, maintenance_info)
            self.update_maintenance('deleted', maintenance_index, maintenance_info)

    def delete_all_maintenances(self):
        maintenance_list = self.get_maintenance_list()

        for maintenance in maintenance_list:
            maintenance_index = maintenance['maintenanceIndex']
            maintenance_name = maintenance['name']

            if maintenance_name:
                self.update_maintenance('cancelled', maintenance_index, maintenance)
                self.update_maintenance('deleted', maintenance_index, maintenance)

    def execute(self, vars):
        command = vars['cmd']
        args = vars['args']

        if command == 'trigger.optimisation':
            s = self.trigger_path_optimisation()
        elif command == 'create.device.maintenance':
            self.put_device_in_maintenance(args, 'maintenance_{}'.format(args))
        elif command == 'delete.device.maintenance':
            self.delete_maintenance('maintenance_{}'.format(args))
        else:
            logger.error('Undefined northstar command ... skipping - %s', command)