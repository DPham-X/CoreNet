import json
import logging
import time
from datetime import datetime, timedelta

import requests
import yaml

# Constants
DATABASE_HOST = 'http://10.49.227.135'
DATABASE_PORT = 5000
EXECUTOR_HOST = 'http://10.49.227.135'
EXECUTOR_PORT = 5001
EVALUATION_INTERVAL = 60  # Seconds
EVALUATION_CONFIG_FILE = 'evaluation_config.yaml'
EVALUATION_LINK_FILE = 'evaluation_link.yaml'

# Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)

logger.addHandler(handler)


class Link(object):
    def __init__(self, link):
        """Creates a link object to track the status of two coupled
        events.

        :param link: Coupling information between first and second events
        :type link: dict: {1: 'First event name',
                           2: 'Second event name',
                           'default': 'default event'}
        """
        self.links = {}
        event_name_1 = link[1]
        event_name_2 = link[2]

        # Set the status of both events as unactivated
        self.links[event_name_1] = False
        self.links[event_name_2] = False

        # Sets the default event as activated
        if 'default' in link.keys():
            default_event = link['default']
            if default_event == 1:
                self.links[event_name_1] = True
            elif default_event == 2:
                self.links[event_name_1] = True

    def _get_other_event(self, link_dict, i_event_name):
        """Gets the name of the other event in the links dict

        :param link_dict: Link information with couple events and their status
        :type link_dict: dict
        :param i_event_name: The unwanted event name
        :type i_event_name: str

        :return: The other event name to which i_event_name was coupled to

        :raises KeyError: If the other event can not be found
        """
        for event_name, _ in link_dict.items():
            if event_name != i_event_name:
                return event_name
        raise KeyError('Could not find the coupled event of {}'.format(i_event_name))

    def update_link(self, event_name):
        """Updates the link information when given an event name

        If the event has not been previously activated then will become
        active and the other event to which it is coupled to will become
        inactive.

        :param event_name: Name of event
        :type event_name: str

        :return: The status for the input event, [True] if its no active and
                 [False] otherwise
        """
        if self.links[event_name] == False:
            self.links[event_name] = True
            other_link = self._get_other_event(self.links, event_name)
            self.links[other_link] = False
            return True
        logger.info('%s is already active', event_name)
        return False

    def __repr__(self):
        """Prints a table formatted version of the Link"""
        links = [link for link in self.links.keys()]
        link_1 = links[0]
        link_2 = links[1]
        f = 'Status | Link Name\n----------------\n{}   | {}\n{}   | {}'
        return f.format(self.links[link_1], link_1, self.links[link_2], link_2)


class Evaluator(object):
    def __init__(self):
        """Constantly checks the database for events and will set up
        execution commands depending on the event
        """
        self.configs = None
        self.events = None
        self.links = {}
        self.database_url = '{}:{}'.format(DATABASE_HOST, DATABASE_PORT)
        self.execution_url = '{}:{}/exec_command'.format(EXECUTOR_HOST, EXECUTOR_PORT)
        self.get_events_interval_url = '{}/get_events_interval'.format(self.database_url)

        # Load up inital configurations
        self._import_config()
        self._import_links()

        # Starting execution delta of 0
        interval_s = datetime(1,1,1)
        interval_e = datetime(1,1,1)
        evaluation_duration = interval_s - interval_e

        while True:
            # StartTime = CurrentTime - TimeInThePast - TimeTakenToEvaluate
            s = (datetime.now() - timedelta(seconds=EVALUATION_INTERVAL) - evaluation_duration).isoformat()
            # EndTime = CurrentTime
            e = datetime.now().isoformat()

            interval_s = datetime.now()
            self._get_events(s, e)
            self._evaluate_events()
            interval_e = datetime.now()

            evaluation_duration = interval_s - interval_e
            time.sleep(60)

    def _import_config(self):
        """Imports the Evaluation configuration which contain all the predefined
        settings for determining what to do with each event

        :raises FileNotFoundError: If config file is empty
        """
        config = None
        with open(EVALUATION_CONFIG_FILE, 'r') as conf:
            config = yaml.load(conf.read())
            logging.info('Imported \'%s\'', EVALUATION_CONFIG_FILE)
        if not config:
            raise FileNotFoundError('Could not load config')

    def _import_links(self):
        """Imports the Link configuration settings to determine which pair of
        events are connected together

        :raises FileNotFoundError: If link file is empty
        """
        e_links = None
        with open(EVALUATION_LINK_FILE, 'r') as f_links:
            e_links = yaml.load(f_links.read())
        if not e_links:
            raise FileNotFoundError('Could not load config')

        for e_link in e_links:
            l = Link(e_link)
            logger.info('Imported Link: %s <-> %s', e_link[1], e_link[2])
            self.links[e_link[1]] = l
            self.links[e_link[2]] = l


    def _get_events(self, start_time, end_time):
        """REST call to the database to retrieve a list of events for a
        specified interval

        :params start_time: Initial period for when to get the events
        :type start_time: str
        :params end_time: Final period for when to get the events
        :type end_time: str
        """
        self.events = []
        # Ensure start and end times are in iso8601 format
        query_url = '{}?start_time={}&end_time={}'.format(self.get_events_interval_url, start_time, end_time)
        logger.info('Querying {}'.format(query_url))
        r = requests.get(query_url, timeout=10)
        if r.status_code != 200:
            logger.error('Query was unsuccessful')
            return
        logger.info('Query successful')
        self.events = r.json()

    def _evaluate_events(self):
        """Determine which events to execute based on the configuration that
        was previously imported.
        """
        if not self.events:
            logger.error('Could not find any events')
            return

        unique_events = set(self.events)
        logger.debug('Unique events: {}'.format(unique_events))

        for config in self.configs:
            if set(config['events']).issubset(unique_events):
                logger.debug('Executing commands for %s', config['name'])
                status = self._check_if_already_executed(name=config['name'])
                if status == False:
                    logger.debug('Skipping')
                    continue
                self._execute_commands(config)

    def _check_if_already_executed(self, name):
        """Determine if the event has already been previously executed
        :param name: Event name
        :type name: str

        :return :  [True] if the event has not been executed yet; [False] otherwise
        """
        logger.debug('Getting associated Link settings')
        link = self.links[name]
        status = link.update_link(name)
        return status

    def _execute_commands(self, config):
        """POST message to the Execution endpoint. Sends an Execution
        message to the Executor to carry out a series of actions based
        on what was evaluated

        :param config: Execution configuration for the defined event, imported from
                       the evaluation config.
        :type config: dict
        """
        try:
            # Format json output
            headers = {
                'Content-Type': 'application/json',
            }
            body = {
                'evaluation_name': config['name'],
                'binded_events': json.dumps(config['events']),
                'commands': json.dumps(config['commands']),
            }

            # Sent Execution message to Executor
            logger.info('Posting to {}, {}'.format(self.execution_url, body))
            r = requests.post(self.execution_url, json=body, headers=headers)
        except Exception as e:
            logger.error(e)


if __name__ == '__main__':
    Evaluator()
