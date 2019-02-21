import ast
import json
import logging
import time
import uuid
from datetime import datetime

import requests
from flask import Flask, json, request
from flask_restful import Api, Resource, reqparse

from lib.junos_cli_trigger import JunosCliTrigger
from lib.northstar_trigger import NorthstarTrigger

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

ns_logger = logging.getLogger('lib.northstar_trigger')
ns_logger.setLevel(logging.DEBUG)
ns_logger.addHandler(handler)

jcli_logger = logging.getLogger('lib.junos_cli_trigger')
jcli_logger.setLevel(logging.DEBUG)
jcli_logger.addHandler(handler)

app = Flask(__name__)
api = Api(app)
parser = reqparse.RequestParser()

ns = NorthstarTrigger()
jcli = JunosCliTrigger()

class ExecuteCommands(Resource):
    def get(self):
        pass

    def post(self):
        parser.add_argument('commands', action='append')
        parser.add_argument('evaluation_name', action='append')
        parser.add_argument('binded_events', action='append')
        args = parser.parse_args()
        commands = args.commands
        name = args.evaluation_name

        binded_events = args.binded_events
        time = datetime.now().isoformat()

        for command_str in commands:
            vars = ast.literal_eval(command_str)
            if 'cli' in vars:
                jcli.execute(vars['cli'])
            elif 'northstar' in vars:
                ns.execute(vars['northstar'])
            else:
                logger.error('Command type not supported: %s', vars)

        headers = {
            'Content-Type': 'application/json'
        }
        body = {
            'uuid': str(uuid.uuid4()),
            'name': name,
            'binded_events': json.dumps(binded_events),
            'time': str(time),
            'commands': json.dumps(commands)
        }
        r = requests.post('http://127.0.0.1:5000/executions', json=body, headers=headers)
        logger.info('Sent execution event %s', r.status_code)


api.add_resource(ExecuteCommands, '/exec_command')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)
