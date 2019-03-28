import logging
from datetime import datetime, timedelta
import yaml
import requests

# Constants
NORTHSTAR_AUTH = 'config/auth.yaml'

# Logging
logger = logging.getLogger(__name__)


class NorthstarTrigger(object):
    access_token = None
    token_type = None
    base_url = None
    username = None
    password = None
    verify = False

    def __init__(self, config_file=NORTHSTAR_AUTH):
        """NorthStar REST API Translator"""
        self._import_variables(config_file)
        logger.info('Started NorthStarTrigger')

    def _import_variables(self, config_file):
        """Imports authentication credentials for NorthStar"""
        with open(config_file) as file:
            imported_vars = yaml.load(file.read())

        self.base_url = 'https://{}:{}'.format(imported_vars['hostname'], imported_vars['port'])
        self.username = imported_vars['username']
        self.password = imported_vars['password']

    def _get_token(self):
        """Requests the Token needed for making NorthStar API calls

        :raises ConnectionError: When there is a problem in connecting to the Authentication API
        """
        payload = {
            'grant_type': 'password',
            'username': self.username,
            'password': self.password
        }
        token_url = self.base_url + '/oauth2/token'
        logger.info('Connecting to {} with username: {}'.format(self.base_url, self.username))
        r = requests.post(token_url, data=payload, verify=self.verify, auth=(self.username, self.password))

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
        """Gets the node ID corresponding to the Router name

        :param name: Router name
        :type name: str
        :param nodes: Northstar node list
        :type nodes: list
        :return: Node ID, [None] if router is not in the node
        :rtype: int
        """
        for node in nodes:
            if 'hostName' not in node.keys():
                continue
            if node['hostName'] == name:
                return node['nodeIndex']
        return None

    def get_topology_elements(self):
        """Retrieves a list of network nodes from the NorthStar API

        :raises ConnectionError: When there is a problem in connecting to the NorthStar API
        :return: List of nodes for each network device
        :rtype: list
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
            raise ConnectionError('Could not get NorthStar topology elements. {}'.format(e))

        return topology_information

    def get_links(self):
        """Retrieves the link information for every link in the network

        :raises ConnectionError: When there is a problem in connecting to the NorthStar API
        :return: List of NorthStar Links
        :rtype: list
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
            raise ConnectionError('Could not get NorthStar links. {}'.format(e))

        logger.debug('Received the following links:')
        logger.debug([link['id'] for link in link_information])

        return link_information

    def create_new_maintenance(self, event_name, index):
        """Sets a device into maintenance given their index in the topology list

        :param event_name: Name of the maintenance event
        :type event_name: str
        :param index: Index of the network device as found in the network node list
        :type index: int
        :returns output and status
        :type returns: str, bool
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
            output ='Maintenance name already in use {}... skipping'.format(event_name)
            logger.info(output)
            return output, True

        logger.debug('Putting device into maintenance')
        logger.debug('Posting to: {}'.format(maintenance_url))
        r = requests.post(maintenance_url, json=body, headers=headers, verify=self.verify)
        if r.status_code != 201:
            return r.json(), False
        logger.info('Successfully created maintenance event, Name:{} Start:{} End:{}'.format(event_name, start_time, end_time))
        return r.json(), True

    def get_maintenance_list(self):
        """Retrieves all the maintenances from the NorthStar API

        :return: List of maintenances on NorthStar
        :rtype: list
        """
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
        """Updates an existing maintenance with a new status

        :param status: Status of the maintenance to be updated to
        :type status: str
        :param index: Node ID in the maintenance list
        :type index: int
        :param info: Existing maintenance object in json
        :type info: str
        """
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
        """Forces NorthStar to recalculate optimal paths

        :return: Output message if there is one or [False] if it failed
        :rtype: str or bool
        """
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
            response = r.json()
            assert r.status_code == 200, r.status_code
        except AssertionError:
            # Northstar triggers that have already happened are still considered successful
            if 'ignored' in response:
                return response, True
            if response:
                return response, False
            return {'Error': 'Could not trigger path optimisation, {}'.format(r.status_code)}, False
        logger.info(response['result '])
        return response, True

    def put_device_in_maintenance(self, router_name, event_name):
        """Puts a specific network device into maintenance mode

        :param router_name: Name of the network device to put into maintenance
        :type router_name: str
        :param event_name: Name of the maintenace
        :type event_name: str
        :return: Message saying that the maintenance was created
        :rtype: str
        """
        topology_info = self.get_topology_elements()
        index = self._node_id_from_name(router_name, topology_info)
        if not isinstance(index, int):
            output = 'Could not find device \'{}\''.format(router_name)
            logger.error(output)
            return output, False
        logger.debug('Creating new maintenance for \'{}\''.format(router_name))
        output, status = self.create_new_maintenance(event_name, index)
        if status is False:
            return output, False
        return 'Created new maintenance for \'{}\'.\n{}'.format(router_name, output), True

    def delete_maintenance(self, event_name):
        """Deletes a maintenance from NorthStar by setting it to 'cancelled' first
        and then changing that status to 'deleted'

        :param event_name: Nam eof the maintenance
        :type event_name: str
        :return: Message saying that the maintenance was deleted
        :rtype: str
        """
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

        return '{} has been deleted'.format(event_name), True

    def delete_all_maintenances(self):
        """Deletes all the maintenances on NorthStar by setting them all to 'cancelled'
        and then to 'deleted'"""
        maintenance_list = self.get_maintenance_list()

        for maintenance in maintenance_list:
            maintenance_index = maintenance['maintenanceIndex']
            maintenance_name = maintenance['name']

            if maintenance_name:
                self.update_maintenance('cancelled', maintenance_index, maintenance)
                self.update_maintenance('deleted', maintenance_index, maintenance)

    def execute(self, vars):
        """Executes NorthStarTrigger valid commands

        Supported commands
        ------------------
        - trigger.optimisation
        - create.device.maintenance
        - delete.device.maintenance

        :param vars: Has all information on the action to take including
                     the command to be run and arguments associated with it
        :type vars: dict
        :return: Output of the command that was executed
        :rtype: str
        """
        command = vars['cmd']
        args = vars['args']

        if command == 'trigger.optimisation':
            output, status = self.trigger_path_optimisation()
        elif command == 'create.device.maintenance':
            output, status = self.put_device_in_maintenance(args, 'maintenance_{}'.format(args))
        elif command == 'delete.device.maintenance':
            output, status = self.delete_maintenance('maintenance_{}'.format(args))
        else:
            logger.error('Undefined northstar command ... skipping - %s', command)
            return '', False
        return output, status
