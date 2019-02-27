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

class Link(object):
    def __init__(self, link):
        self.links = {}

        self.links[link[1]] = False
        self.links[link[2]] = False

        if 'default' in link.keys():
            default_link = link['default']
            if default_link == 1:
                self.links[link[1]] = True
            elif default_link == 2:
                self.links[link[2]] = True

    def _get_other_key(self, d, k):
        for key, value in d.items():
            if key != k:
                return key
        raise KeyError('Could not find other key')

    def update_link(self, link):
        if self.links[link] == False:
            self.links[link] = True
            other_link = self._get_other_key(self.links, link)
            self.links[other_link] = False
            return True
        logger.info('Already activated')
        return False

    def __repr__(self):
        links = [link for link in self.links.keys()]
        link_1 = links[0]
        link_2 = links[1]
        f = 'Status | Link Name\n----------------\n{}   | {}\n{}   | {}'
        return f.format(self.links[link_1], link_1, self.links[link_2], link_2)


class Evaluator(object):
    def __init__(self):
        self.configs = None
        self.events = None
        self.links = {}
        self.database_url = 'http://10.49.227.135:5000'
        self.execution_url = 'http://10.49.227.135:5001/exec_command'
        self.running_confs = []
        self._import_config()
        self._import_links()

        interval_s = datetime(1,1,1)
        interval_e = datetime(1,1,1)

        while True:
            s = (datetime.now() - timedelta(seconds=60) - (interval_e - interval_s)).isoformat()
            e = datetime.now().isoformat()
            interval_s = datetime.now()
            self._get_events(s, e)
            self._evaluate_events()
            interval_e = datetime.now()
            time.sleep(60)

    def _import_config(self):
        config = None
        with open('evaluation_config.yaml', 'r') as conf:
            config = yaml.load(conf.read())
        if not config:
            raise FileNotFoundError('Could not load config')
        self.configs = config

        for config in self.configs:
            config['status'] = 'inactive'

    def _import_links(self):
        e_links = None
        with open('evaluation_link.yaml', 'r') as f_links:
            e_links = yaml.load(f_links.read())
        if not e_links:
            raise FileNotFoundError('Could not load config')

        for e_link in e_links:
            l = Link(e_link)
            logger.info('Imported Link: %s <-> %s', e_link[1], e_link[2])
            self.links[e_link[1]] = l
            self.links[e_link[2]] = l


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
        logger.info('Unique events: {}'.format(unique_events))

        for config in self.configs:
            if set(config['events']).issubset(unique_events):
                logger.debug('Executing commands for %s', config['name'])
                status = self.check_if_already_executed(name=config['name'])
                if status == False:
                    logger.debug('Skipping')
                    continue
                self.execute_commands(config, self.events)

    def check_if_already_executed(self, name):
        logger.debug('Getting associated Link settings')
        link = self.links[name]
        logger.debug(link)
        logger.debug('Updating link')
        status = link.update_link(name)
        logger.debug('Link has been updated')
        logger.debug(link)
        return status

    def execute_commands(self, config, events):
        headers = {
            'Content-Type': 'application/json',
        }
        if config['name'] in self.running_confs:
            logger.info('Command is already running: %s', config['name'])

        self.running_confs.append(config['name'])
        body = {
            'evaluation_name': config['name'],
            'binded_events': json.dumps(config['events']),
            'commands': json.dumps(config['commands']),
        }
        try:
            logger.info('Posting to {}, {}'.format(self.execution_url, body))
            r = requests.post(self.execution_url, json=body, headers=headers)
        except Exception as e:
            logger.error(e)

        self.running_confs.remove(config['name'])


if __name__ == '__main__':
    Evaluator()
