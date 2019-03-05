import logging
import uuid
from datetime import datetime

import requests
from flask import Flask, json
from flask_restful import Api, Resource, reqparse

from lib.northstar_trigger import NorthstarTrigger
from lib.junos_cli_trigger import JunosCliTrigger
from lib.junos_backup_trigger import BackupTrigger
from lib.junos_trigger import JunosTrigger

# Constants
HOST = '0.0.0.0'
PORT = 5001
DATABASE_URL = 'http://10.49.227.135'
DATABASE_PORT = 5000

# Logging
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

ns_logger = logging.getLogger('lib.northstar_trigger')
ns_logger.setLevel(logging.DEBUG)
ns_logger.addHandler(handler)

jcli_logger = logging.getLogger('lib.junos_cli_trigger')
jcli_logger.setLevel(logging.DEBUG)
jcli_logger.addHandler(handler)

jbt_logger = logging.getLogger('lib.junos_backup_trigger')
jbt_logger.setLevel(logging.DEBUG)
jbt_logger.addHandler(handler)

jt_logger = logging.getLogger('lib.junos_trigger')
jt_logger.setLevel(logging.DEBUG)
jt_logger.addHandler(handler)

# Flask Settings
app = Flask(__name__)
api = Api(app)
parser = reqparse.RequestParser()

# Init Execution modules
ns = NorthstarTrigger()
jcli = JunosCliTrigger()
bt = BackupTrigger()
jt = JunosTrigger()


class ExecuteCommands(Resource):
    def post(self):
        """POST method for handling any decisions made by the Evaluator, executing
        all the required commands and storing the results into the Database

        Supported command types:
        - northstar: Execute NorthStar SDWAN commands
        - cli:  Execute Junos RPC commands
        - junos_backup: Backup Junos configurations
        - junos: Push Junos configurations

        :param commands: List of actions to take
        :param evaluation_name: Name of Evaluation that is to be taken
        :param binded_events: Set of events which triggered the decision
        """
        parser.add_argument('commands', type=str)
        parser.add_argument('evaluation_name', type=str)
        parser.add_argument('binded_events', type=str)

        args = parser.parse_args()

        name = args.evaluation_name
        binded_events = args.binded_events
        time = datetime.now().isoformat()
        status = 'Completed'
        new_uuid = str(uuid.uuid4())
        python_commands = json.loads(args.commands)

        for i, command in enumerate(python_commands):
            try:
                output = ''
                if 'cli' == command['type']:
                    logger.info('Found CLI command')
                    output = jcli.execute(command)
                elif 'northstar' == command['type']:
                    logger.info('Found Northstar command')
                    output = ns.execute(command)
                elif 'junos_backup' == command['type']:
                    logger.info('Found JunosBackup command')
                    output = bt.execute(command, new_uuid)
                elif 'junos' == command['type']:
                    logger.info('Found JunosTrigger command')
                    output = jt.execute(command)
                else:
                    logger.error('Command type not supported: %s', command['type'])
                    status = 'Failed'
                    raise KeyError
            except KeyError as e:
                logger.error('An error occurred %s', e)
                status = 'Failed'
                python_commands[i]['output'] = 'An error occured'
                break
            else:
                python_commands[i]['output'] = str(output)

                if not output:
                    status = 'Failed'
                    python_commands[i]['output'] = 'An error occured'

                if status == 'Failed':
                    break

        headers = {
            'Content-Type': 'application/json'
        }
        body = {
            'uuid': new_uuid,
            'name': name,
            'binded_events': binded_events,
            'time': str(time),
            'commands': json.dumps(python_commands),
            'status': status
        }
        r = requests.post('{}:{}/executions'.format(DATABASE_URL, DATABASE_PORT), json=body, headers=headers)
        logger.info('Sent execution event %s', r.status_code)


# Routes for Executor API
api.add_resource(ExecuteCommands, '/exec_command')


if __name__ == '__main__':
    app.run(host=HOST, debug=False, port=PORT, use_reloader=False)
