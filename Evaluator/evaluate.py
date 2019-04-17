import json
import logging
import time
import threading
from datetime import datetime, timedelta
import requests
import yaml

# Constants
DATABASE_URL = 'http://0.0.0.0'
DATABASE_PORT = 5000
EXECUTOR_URL = 'http://0.0.0.0'
EXECUTOR_PORT = 5001
EVALUATION_INTERVAL = 20  # Seconds
EVALUATION_CONFIG_FILE = 'evaluation_config.yaml'
EVALUATION_LINK_FILE = 'evaluation_link.yaml'

# Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)

logger.addHandler(handler)


class Link(object):
    def __init__(self, link, configs=[None, None]):
        """Creates a link object to track the status of two coupled
        events.

        :param link: Coupling information between first and second events
        :type link: dict: {1: 'First event name',
                           2: 'Second event name',
                           'default': 'default event'}
        """
        self.links = {}
        self.configs = {}
        self.timeout = 0
        event_name_1 = link[1]
        event_name_2 = link[2]

        # Set the status of both events as unactivated
        self.links[event_name_1] = False
        self.links[event_name_2] = False

        # Store the evaluation configuration in the link
        self.configs[event_name_1] = configs[0]
        self.configs[event_name_2] = configs[1]

        # Sets the default event as activated
        if 'default' in link.keys():
            default_event = link['default']
            if default_event == 1:
                self.links[event_name_1] = True
            elif default_event == 2:
                self.links[event_name_1] = True

        # Set timeout if it exists
        if 'timeout' in link.keys():
            self.timeout = link['timeout']

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

    def update_link(self, event_name, config):
        """Updates the link information when given an event name

        If the event has not been previously activated then it will become
        active and the other event to which it is coupled to will become
        inactive.

        :param event_name: Name of event
        :type event_name: str
        :param config: Imported evaluation config
        :type config: dict

        :return: The status for the input event, [True] if its no active and
                 [False] otherwise
        """
        logger.info('%s is %s', event_name, self.links[event_name])
        if self.links[event_name] is False:
            self.links[event_name] = True
            if self.timeout == 0:
                other_link = self._get_other_event(self.links, event_name)
                self.links[other_link] = False
            else:
                # Get other config
                other_event_name = self._get_other_event(self.links, event_name)
                other_config = self.configs[other_event_name]
                self.start_timer(event_name, other_config)
            return True
        # logger.info('%s is already active', event_name)
        return False

    def start_timer(self, event_name, other_config):
        """Spawns a thread which will unlock this link after the defined timeout

        :param event_name: Name of event
        :type event_name: str
        :param other_config: Imported evaluation config
        :type other_config: dict
        """
        logger.info('Starting Reset Thread')
        t = threading.Thread(target=self.reset_timer, args=(event_name, other_config))
        t.start()

    def reset_timer(self, event_name, other_config):
        """Reset the lock and activation for this evaluation"""
        time.sleep(self.timeout)
        self.links[event_name] = False
        logger.info('Resetting \'{}\' back to inactive'.format(event_name))
        Evaluator._send_execution(other_config)

    def __repr__(self):
        """Prints a table formatted version of the Link"""
        links = [link for link in self.links.keys()]
        link_1 = links[0]
        link_2 = links[1]
        f = 'Status | Link Name\n----------------\n{}   | {}\n{}   | {}'
        return f.format(self.links[link_1], link_1, self.links[link_2], link_2)


class Evaluator(object):
    database_url = '{}:{}'.format(DATABASE_URL, DATABASE_PORT)
    execution_url = '{}:{}/exec_command'.format(EXECUTOR_URL, EXECUTOR_PORT)
    get_events_interval_url = '{}/get_events_interval'.format(database_url)

    def __init__(self):
        """Constantly checks the database for events and will set up
        execution commands depending on the event
        """
        self.configs = []
        self.events = None
        self.links = {}

        # Load up inital configurations
        self._import_config()
        self._import_links()

        # Starting execution delta of 0
        interval_s = datetime(1, 1, 1)
        interval_e = datetime(1, 1, 1)
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
            time.sleep(EVALUATION_INTERVAL)

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
        self.configs = config

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
            for i in self.configs:
                if i['name'] == e_link[1]:
                    config1 = i
                if i['name'] == e_link[2]:
                    config2 = i

            link = Link(e_link, [config1, config2])
            logger.info('Imported Link: %s <-> %s', e_link[1], e_link[2])
            self.links[e_link[1]] = link
            self.links[e_link[2]] = link

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
        logger.info('Querying %s', query_url)
        try:
            r = requests.get(query_url, timeout=60)
            if r.status_code != 200:
                logger.error('Query unsuccessful')
                return
        except requests.exceptions.ReadTimeout:
            logger.info('Timed out..')
        else:
            logger.info('Query successful')
            if isinstance(r.json(), list):
                self.events = r.json()
            else:
                logger.error('Something weird was returned')
                logger.error(r.json)

    def _evaluate_events(self):
        """Determine which events to execute based on the configuration that
        was previously imported.
        """
        if not self.events:
            logger.error('Could not find any events')
            return

        unique_events = set([event['name'] for event in self.events])
        logger.debug('Unique events: %s', str(unique_events))

        for config in self.configs:
            events = config['events']
            if not events:
                continue
            if set(events).issubset(unique_events):
                logger.debug('Executing commands for %s', config['name'])
                status = self._check_if_already_executed(config)
                if status is False:
                    # logger.debug('%s already executed ... skipping', config['name'])
                    continue
                self._send_execution(config)

    def _check_if_already_executed(self, config):
        """Determine if the event has already been previously executed
        :param config: Imported evaluation configuration
        :type name: dict

        :return :  [True] if the event has not been executed yet; [False] otherwise
        """
        logger.debug('Getting associated Link settings')
        name = config['name']
        link = self.links[name]
        status = link.update_link(name, config)
        return status

    @staticmethod
    def _send_execution(config):
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
            logging.info('Executing %s!', config['name'])
            logger.info('Posting to %s', Evaluator.execution_url)
            r = requests.post(Evaluator.execution_url, json=body, headers=headers)
            if r.status_code != 200:
                logger.error('Could not send executions to the Executor, %s', r.status_code)
        except Exception as e:
            logger.error(e)


if __name__ == '__main__':
    Evaluator()
