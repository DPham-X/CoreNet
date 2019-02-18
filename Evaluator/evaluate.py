import json
import logging
import time
from datetime import datetime, timedelta

import requests
import yaml

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)

logger.addHandler(handler)


class Evaluator(object):
    def __init__(self):
        self.configs = None
        self.events = None
        self.database_url = 'http://localhost:5000'
        self.execution_url = 'http://localhost:5001/exec_command'
        self.running_confs = []
        self._import_config()

        while True:
            s = (datetime.now() - timedelta(seconds=15)).isoformat()
            e = datetime.now().isoformat()
            self._get_events(s, e)
            self._evaluate_events()
            time.sleep(15)

    def _import_config(self):
        config = None
        with open('evaluation_config.yaml', 'r') as conf:
            config = yaml.load(conf.read())
        if not config:
            raise FileNotFoundError('Could not load config')
        self.configs = config

        for config in self.configs:
            config['status'] = 'inactive'

    def _get_events(self, start_time, end_time):
        self.events = []
        # Ensure start and end times are in iso8601 format
        query_url = '{}/get_events?start_time={}&end_time={}'.format(self.database_url, start_time, end_time)
        logger.info('Querying {}'.format(query_url))
        r = requests.get(query_url, timeout=10)
        if r.status_code != 200:
            logger.error('Query was unsuccessful')
            return
        logger.info('Query successful')
        self.events = r.json()

    def _evaluate_events(self):
        if not self.events:
            logger.error('Could not find any events')
            return

        unique_events = set()
        for event in self.events:
            unique_events.add(event['name'])
        logger.debug('Unique events: {}'.format(unique_events))

        for config in self.configs:
            if set(config['events']).issubset(unique_events):
                logger.debug('Executing commands')
                self.execute_commands(config, self.events)

    def execute_commands(self, config, events):
        headers = {
            'Content-Type': 'application/json',
        }
        if config['name'] in self.running_confs:
            logger.info('Command is already running: %s', config['name'])

        self.running_confs.append(config['name'])
        body = {
            'commands': config['commands'],
        }
        try:
            logger.info('Posting to {}, {}'.format(self.execution_url, body))
            r = requests.post(self.execution_url, json=body, headers=headers, timeout=10)
        except Exception as e:
            logger.error(e)

        self.running_confs.remove(config['name'])




if __name__ == '__main__':
    Evaluator()
