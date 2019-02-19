from flask import Flask, json, request
from flask_restful import Resource, Api, reqparse
from lib.northstar_trigger import NorthstarTrigger
import ast
import logging
from lib.junos_cli_trigger import JunosCliTrigger

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
        args = parser.parse_args()
        commands = args.commands

        for command_str in commands:
            vars = ast.literal_eval(command_str)
            if 'cli' in vars:
                jcli.execute(vars['cli'])
            elif 'northstar' in vars:
                ns.execute(vars['northstar'])
            else:
                logger.error('Command type not supported: %s', vars)

api.add_resource(ExecuteCommands, '/exec_command')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)