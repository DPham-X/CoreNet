import ast
import logging
import sys
import threading

from flask import Flask, json, request
from flask_restful import Api, Resource, reqparse

from lib.appformix_collector import AppformixCollector
from lib.junos_collector import JunosCollector


# Constants
HOST = '0.0.0.0'
COLLECTOR_PORT = 5002
DEVICE_CONFIG = 'config/devices.yaml'

# API Parsing
parser = reqparse.RequestParser()

# Flask Settings
app = Flask(__name__)
api = Api(app)

# Logging
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

jc_logger = logging.getLogger('lib.junos_collector')
jc_logger.setLevel(logging.DEBUG)
jc_logger.addHandler(handler)

# Init modules
ac = AppformixCollector()

class Collector(object):
    def __init__(self):
        """Instantiates Collector modules in separate threads to monitor data

        Modules
        -------
        JunosCollector: Monitor Junos network device statuses
        """
        threads = []
        jc_thread = threading.Thread(name='JunosCollector', target=JunosCollector, args=(DEVICE_CONFIG,))
        jc_thread.daemon = True

        threads.append(jc_thread)

        for thread in threads:
            logger.info('Starting Thread: %s', thread.name)
            thread.start()

        app.run(host=HOST, port=COLLECTOR_PORT, debug=False, use_reloader=False)

class AppformixCollectorAPI(Resource):
    def post(self):
        """POST method for AppFormix API interfacing. This will serve as the
        endpoint for an AppFormix webhook, parsing any events/alarms and storing them
        in the database

        :param status: AppFormix status containing details of the notification
        :param spec: AppFormix spec which has details on the specific rule which caused the notification
        :param kind: AppFormix kind which defines the type of notification (Event/Alarm)
        """
        parser.add_argument('status', type=str, location='json')
        parser.add_argument('spec', type=str, location='json')
        parser.add_argument('kind', type=str, location='json')

        args = parser.parse_args()
        status = ast.literal_eval(args.status)
        spec = ast.literal_eval(args.spec)
        kind = str(args.kind)
        ac.send_event(status, spec, kind)

# Routes for the Collector API
api.add_resource(AppformixCollectorAPI, '/appformix')

if __name__ == '__main__':
    Collector()