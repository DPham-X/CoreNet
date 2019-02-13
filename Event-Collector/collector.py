from flask import Flask
from flask_restful import Resource, Api
from lib.junos_collector import JunosCollector

app = Flask(__name__)
api = Api(app)
js = JunosCollector()

class Junos(Resource):
    def get(self):
        interface_status = js.interface_status
        print(interface_status)
        return interface_status

api.add_resource(Junos, '/get_interface_status')

if __name__ == '__main__':
    app.run(debug=True)
