import uuid
from datetime import datetime
import requests
import logging

# Constants
DATABASE_URL = 'http://10.49.227.135'
DATABASE_PORT = 5000

# Logging
logger = logging.getLogger(__name__)

class AppformixCollector(object):
    def __init__(self):
        """Collector module for dealing with AppFormix"""
        self.db_event_endpoint = '{}:{}/create_event'.format(DATABASE_URL, DATABASE_PORT)

    def send_event(self, status, spec, kind):
        """Stores Appformix events to the database as an Event. AppFormix generalised
        notifications will be tagged with an AppFormix prefix for better logging

        Alarm -> AppformixAlarm
        Event -> AppformixEvent

        :param status: AppFormix status containing details of the notification
        :param spec: AppFormix spec which has details on the specific rule which caused the notification
        :param kind: AppFormix kind which defines the type of notification (Event/Alarm)
        """
        if kind == 'Alarm':
            type = 'AppformixAlarm'
        elif kind == 'Event':
            type = 'AppformixEvent'
        else:
            type = 'AppFormixUnknown'

        name = spec['name']
        time = datetime.fromtimestamp(status['timestamp']/ 1e3).isoformat()
        priority = spec['severity']
        body = status

        event = self._create_event(name, time, type, priority, body)

        headers = {
            'Content-Type': 'application/json',
        }

        r = requests.request('POST', self.db_event_endpoint, json=event, headers=headers)
        if r.status_code != 201:
            logger.error('Coud not add the AppFormix event to the database. %s', r.status_code)

    def _create_event(self, name, time, type, priority, body):
        """Generates a Database compatible Event object

        :param uuid: UUID of the new Event
        :param time: Timestamp of when the Event occured in UTC
        :param name: Name of the Event which occured
        :param type: Type of Event which occured (eg. CLI/APPFORMIX)
        :param priority: Priority of the Event (eg. INFORMATION/WARNING/CRITICAL)
        :param body: Any other extra information related to the Event
        """
        event = {
            'uuid': str(uuid.uuid4()),
            'time': time,
            'name': name,
            'type': type,
            'priority': priority,
            'body': body,
        }
        return event