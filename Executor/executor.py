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
from lib.backup_trigger import BackupTrigger

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
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
bt = BackupTrigger()


class ExecuteCommands(Resource):
    def post(self):
        parser.add_argument('commands', type=str)
        parser.add_argument('evaluation_name', type=str)
        parser.add_argument('binded_events', type=str)
        args = parser.parse_args()
        commands = args.commands
        name = args.evaluation_name
        binded_events = args.binded_events
        time = datetime.now().isoformat()
        status = 'Completed'
        uuid = str(uuid.uuid4())

        for vars in json.loads(commands):
            try:
                if 'cli' in vars:
                    logger.info('Found CLI command')
                    jcli.execute(vars['cli'])
                elif 'northstar' in vars:
                    logger.info('Found Northstar command')
                    ns.execute(vars['northstar'])
                elif 'junos_backup' in vars:
                    logger.info('Found JunosBackup command')
                    bt.execute(vars['junos_backup'], uuid)
                else:
                    logger.error('Command type not supported: %s', vars)
                    status = 'Failed'
            except KeyError as e:
                logger.error('An error occurred %s', e)
                status = 'Failed'

        headers = {
            'Content-Type': 'application/json'
        }
        body = {
            'uuid': uuid,
            'name': name,
            'binded_events': binded_events,
            'time': str(time),
            'commands': commands,
            'status': status
        }
        r = requests.post('http://127.0.0.1:5000/executions', json=body, headers=headers)
        logger.info('Sent execution event %s', r.status_code)


api.add_resource(ExecuteCommands, '/exec_command')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)
