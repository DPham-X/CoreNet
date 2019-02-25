import uuid
from datetime import datetime
import requests
import logging

logger = logging.getLogger(__name__)


class AppformixCollector(object):
    def __init__(self):
        self.db_url = 'http://127.0.0.1:5000/create_event'

    def send_event(self, status, spec, kind):
        if kind == 'Alarm':
            type = 'AppformixAlarm'
        elif kind == 'Event':
            type = 'AppformixEvent'
        else:
            type = 'AppFormixUnknown'

        name = spec['name']
        time = datetime.fromtimestamp(status['timestamp']/ 1e3).isoformat()
        priority = spec['severity']
        body = status['metaData']

        event = self._create_event(name, time, type, priority, body)

        headers = {
            'Content-Type': 'application/json',
        }

        requests.request('POST', self.db_url, json=event, headers=headers)

    def _create_event(self, name, time, type, priority, body):
        event = {
            'uuid': str(uuid.uuid4()),
            'time': time,
            'name': name,
            'type': type,
            'priority': priority,
            'body': body,
        }
        return event