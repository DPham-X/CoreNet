import logging
from glob import glob

from flask import Flask, json, request
from flask_cors import CORS
from flask_restful import Api, Resource, reqparse
from flask_sqlalchemy import SQLAlchemy
from gevent.pywsgi import WSGIServer
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from db_models import Event, Execution, db

# Constants
DATABASE_NAME = 'core.db'
HOST = '0.0.0.0'
DB_PORT = 5000

# Flask Settings
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}'.format(DATABASE_NAME)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
engine = create_engine('sqlite:///{}'.format(DATABASE_NAME), convert_unicode=True)
db.session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine,
                                         expire_on_commit=False))
api = Api(app)
CORS(app)
db.app = app
db.init_app(app)

# API Parsing
parser = reqparse.RequestParser()

# Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)

logger.addHandler(handler)


def initialise_db(db_name):
    """Creates a new database if an existing one cannot be found

    :param db_name: Filename of the database
    :type db_name: str
    """
    if db_name not in glob('*'):
        logger.info('Creating new database \'%s\'', db_name)
        db.create_all()
    # else:
        # logger.info('Existing database \'%s\' already exists', db_name)


def add_event_to_db(event):
    """Adds and commits new entries into the core databse

    :param event: Database model that has been filled out
    :type event: db.model object
    """
    try:
        engine.execute(Event.__table__.insert(),[{
            'uuid': event.uuid,
            'time': event.time,
            'name': event.name,
            'type': event.type,
            'priority': event.priority,
            'body': event.body,
        }])
    except IntegrityError as e:
        logger.error('UUID might already be in the database (ignoring)\n %s', e)
        return False
    else:
        logging.info('Sucessfully added Event: {}'.format(event.uuid))
    return True

def add_execution_to_db(execution):
    """Adds and commits new entries into the core databse

    :param execution: Database model that has been filled out
    :type execution: db.model object
    """
    try:
        engine.execute(Execution.__table__.insert(),[{
            'uuid': execution.uuid,
            'name': execution.name,
            'binded_events': execution.binded_events,
            'time': execution.time,
            'commands': execution.commands,
            'status': execution.status,
        }])
    except IntegrityError as e:
        logger.error('UUID might already be in the database (ignoring)\n %s', e)
        return False
    else:
        logging.info('Sucessfully added Execution: {}'.format(execution.uuid))
    return True

class DBCreateEvent(Resource):
    def post(self):
        """POST method for storing new Event entries into the database

        :param uuid: UUID of the new Event
        :param time: Timestamp of when the Event occured in UTC
        :param name: Name of the Event which occured
        :param type: Type of Event which occured (eg. CLI/APPFORMIX)
        :param priority: Priority of the Event (eg. INFORMATION/WARNING/CRITICAL)
        :param body: Any other extra information related to the Event

        :return: A Success message if the Event was added or an Error otherwise
        """
        parser.add_argument('uuid', type=str)
        parser.add_argument('time', type=str)
        parser.add_argument('name', type=str)
        parser.add_argument('type', type=str)
        parser.add_argument('priority', type=str)
        parser.add_argument('body', type=str)
        args = parser.parse_args()

        new_event = Event(uuid=str(args['uuid']),
                          time=str(args['time']),
                          name=str(args['name']),
                          type=str(args['type']),
                          priority=str(args['priority']),
                          body=str(args['body']))
        status = add_event_to_db(new_event)
        if not status:
            return {'Error': 'Could not add event to database'}, 400
        return {'Success': 'New event added with id {}'.format(args['uuid'])}, 201


class DBGetEventsLast(Resource):
    def get(self):
        """GET method that retrieves the 100 most recent Events

        :return: A list of Events"""
        output = []
        try:
            queries = db.session.query(Event).order_by(Event.time.desc()).limit(100)
        except OperationalError:
            return {'Error': 'Database is currently empty'}, 400

        for query in queries:
            query_serialised = {
                'uuid': query.uuid,
                'time': query.time,
                'name': query.name,
                'type': query.type,
                'priority': query.priority,
                'body': json.loads(query.body)
            }
            output.append(query_serialised)
        return output, 200, {'Access-Control-Allow-Origin': '*'}

class DBGetEventsLastCritical(Resource):
    def get(self):
        """GET method that retrieves the 10 most recent Critical events

        :return: A list of Events"""
        output = []
        try:
            queries = db.session.query(Event).order_by(Event.time.desc()).filter(Event.priority == 'critical').limit(10)
        except OperationalError:
            return {'Error': 'Database is currently empty'}, 400

        for query in queries:
            query_serialised = {
                'uuid': query.uuid,
                'time': query.time,
                'name': query.name,
                'type': query.type,
                'priority': query.priority,
                'body': json.loads(query.body)
            }
            output.append(query_serialised)
        return output, 200, {'Access-Control-Allow-Origin': '*'}

class DBGetEventsInterval(Resource):
    def get(self):
        """GET method which retrieves the events for the period between start
        and end time

        :param start_time: The starting timestamp
        :type start_time: datestring object that was converted to int with msec
        :param end_time: The final timestamp
        :type end_time: datestring object that was converted to int with msec

        :return: A list of Events
        """
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        if start_time is None:
            return {'Error': 'start_time has not been defined'}, 400
        if end_time is None:
            return {'Error': 'end_time has not been defined'}, 400

        try:
            queries = db.session.query(Event).filter(Event.time.between(start_time, end_time)).all()
            if not queries:
                return {'Info': 'Could not find any events for the defined interval'}, 200
            output = []
            for query in queries:
                query_serialised = {
                    'uuid': query.uuid,
                    'time': query.time,
                    'name': query.name,
                    'type': query.type,
                    'priority': query.priority,
                    'body': json.loads(query.body)
                }
                output.append(query_serialised)
        except Exception as e:
            return {'Error': str(e)}, 400, {'Access-Control-Allow-Origin': '*'}
        return output, 200, {'Access-Control-Allow-Origin': '*'}


class DBCreateExecution(Resource):
    def post(self):
        """POST method for creating a new Execution entry in the database

        :param uuid: UUID of the new Execution
        :param name: Name of the Execution which occured
        :param binded_events: Events that triggered the Execution
        :param time: Timestamp of when the Execution occured in UTC
        :param commands: Contains all the commands the were executed, their arguments
                         and their output
        :param status: Final status of the Execution (eg. Completed/Failed)

        :return: A Success message if the Execution was added or an Error otherwise
        """
        parser.add_argument('uuid', type=str)
        parser.add_argument('name', type=str)
        parser.add_argument('binded_events', type=str)
        parser.add_argument('time', type=str)
        parser.add_argument('commands', type=str)
        parser.add_argument('status', type=str)

        args = parser.parse_args()

        new_event = Execution(uuid=str(args['uuid']),
                              name=str(args['name']),
                              binded_events=str(args['binded_events']),
                              time=str(args['time']),
                              status=str(args['status']),
                              commands=str(args['commands']))

        db_status = add_execution_to_db(new_event)
        if not db_status:
            return {'Error': 'Could not add execution to database'}, 400
        return {'Success': 'New execution added with id {}'.format(args['uuid'])}, 201


class DBGetExecutionsLast(Resource):
    def get(self):
        """GET method for retrieving the 20 most recent Executions

        :return: a list of Executions
        """
        try:
            queries = db.session.query(Execution).order_by(Execution.time.desc()).limit(20)
        except OperationalError:
            return {'Error': 'Database is currently empty'}, 400
        output = []
        for query in queries:
            query_serialised = {
                'uuid': query.uuid,
                'name': query.name,
                'binded_events': json.loads(query.binded_events),
                'time': query.time,
                'commands': json.loads(query.commands),
                'status': query.status,
            }
            output.append(query_serialised)
        return output, 200, {'Access-Control-Allow-Origin': '*'}

class DBGetExecutionsLast10(Resource):
    def get(self):
        """GET method for retrieving the 20 most recent Executions

        :return: a list of Executions
        """
        try:
            queries = db.session.query(Execution).order_by(Execution.time.desc()).limit(10)
        except OperationalError:
            return {'Error': 'Database is currently empty'}, 400
        output = []
        for query in queries:
            query_serialised = {
                'uuid': query.uuid,
                'name': query.name,
                'binded_events': json.loads(query.binded_events),
                'time': query.time,
                'commands': json.loads(query.commands),
                'status': query.status,
            }
            output.append(query_serialised)
        return output, 200, {'Access-Control-Allow-Origin': '*'}

initialise_db(DATABASE_NAME)

# Routes for the Database API
# Events
api.add_resource(DBCreateEvent,          '/create_event')
api.add_resource(DBGetEventsLast,        '/get_events_last')
api.add_resource(DBGetEventsLastCritical,'/get_events_last_critical')
api.add_resource(DBGetEventsInterval,    '/get_events_interval')
# Executions
api.add_resource(DBCreateExecution,      '/create_execution')
api.add_resource(DBGetExecutionsLast,    '/get_executions_last')
api.add_resource(DBGetExecutionsLast10,  '/get_executions_last10')


if __name__ == '__main__':
    logger.info('Starting WSGI Server %s:%s', HOST, DB_PORT)
    http_server = WSGIServer((HOST, DB_PORT), app)
    http_server.serve_forever()
