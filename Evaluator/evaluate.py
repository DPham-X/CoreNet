import yaml
import requests
import logging
from datetime import datetime, timedelta
import time

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
        self.execution_url = 'http://localhost:5001'
        self.running_confs = []
        self._import_config()

        while True:
            s = (datetime.now() - timedelta(minutes=1)).isoformat()
            e = datetime.now().isoformat()
            self._get_events(s, e)
            self._evaluate_events()
            time.sleep(60)

    def _import_config(self):
        config = None
        with open('evaluation_config.yaml', 'r') as conf:
            config = yaml.load(conf.read())
        if not config:
            raise FileNotFoundError('Could not load config')
        self.configs = config

    def _get_events(self, start_time, end_time):
        # Ensure start and end times are in iso8601 format
        query_url = '{}/get_events?start_time={}&end_time={}'.format(self.database_url, start_time, end_time)
        r = requests.get(query_url)
        if r.status_code != 200:
            logger.error('Query was unsuccessful')
        self.events = r.json()

    def _evaluate_events(self):
        unique_events = set()
        for event in self.events:
            unique_events.add(event['name'])

        for config in self.configs:
            config_event = set(config['events'])
            if config_event == unique_events:
                self.execute_commands(config, self.events)

    def execute_commands(self, config, events):
        headers = {
            'Content-Type': 'application/json',
        }
        if config['name'] in self.running_confs:
            logger.info('Command is already running: %s', config['name'])

        self.running_confs.append(config['name'])
        requests.post(self.execution_url, json=config['commands'], headers=headers)
        self.running_confs.remove(config['name'])




if __name__ == '__main__':
    Evaluator()