import ast
import logging
import sys
import threading

from flask import Flask, json, request
from flask_restful import Api, Resource, reqparse

from lib.appformix_collector import AppformixCollector
from lib.junos_collector import JunosCollector

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

jc_logger = logging.getLogger('lib.junos_collector')
jc_logger.setLevel(logging.DEBUG)
jc_logger.addHandler(handler)


app = Flask(__name__)
api = Api(app)

parser = reqparse.RequestParser()

ac = AppformixCollector()

class Collector(object):
    def __init__(self):
        threads = []
        jc_thread = threading.Thread(name='JunosCollector', target=JunosCollector, args=('config/devices.yaml',))
        jc_thread.daemon = True

        threads.append(jc_thread)

        for thread in threads:
            logger.info('Starting Thread: %s', thread.name)
            thread.start()


        app.run(host='0.0.0.0', port=5002, debug=True, use_reloader=False)

class AppformixCollectorAPI(Resource):
    def post(self):
        parser.add_argument('status', type=str, location= 'json')
        parser.add_argument('spec', type=str, location= 'json')
        parser.add_argument('kind', type=str, location= 'json')

        args = parser.parse_args()
        status = ast.literal_eval(args.status)
        spec = ast.literal_eval(args.spec)
        kind = str(args.kind)
        ac.send_event(status, spec, kind)

api.add_resource(AppformixCollectorAPI, '/appformix')


if __name__ == '__main__':
    Collector()