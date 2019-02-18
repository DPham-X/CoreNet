from flask import Flask, json, request
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api, reqparse
from glob import glob
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.attributes import QueryableAttribute
import ast

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///core.db'
db = SQLAlchemy(app)
api = Api(app)

parser = reqparse.RequestParser()


class Event(db.Model):
    uuid = db.Column(db.String(37), unique=True, primary_key=True, nullable=False)
    time = db.Column(db.String(27), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    priority = db.Column(db.String(20), nullable=True)
    body = db.Column(db.String(100000), nullable=True)

    def to_dict(self, show=None, _hide=[], _path=None):
        """Return a dictionary representation of this model."""

        show = show or []

        hidden = self._hidden_fields if hasattr(self, "_hidden_fields") else []
        default = self._default_fields if hasattr(self, "_default_fields") else []
        default.extend(['uuid', 'time', 'name', 'type', 'priority', 'body'])

        if not _path:
            _path = self.__tablename__.lower()

            def prepend_path(item):
                item = item.lower()
                if item.split(".", 1)[0] == _path:
                    return item
                if len(item) == 0:
                    return item
                if item[0] != ".":
                    item = ".%s" % item
                item = "%s%s" % (_path, item)
                return item

            _hide[:] = [prepend_path(x) for x in _hide]
            show[:] = [prepend_path(x) for x in show]

        columns = self.__table__.columns.keys()
        relationships = self.__mapper__.relationships.keys()
        properties = dir(self)

        ret_data = {}

        for key in columns:
            if key.startswith("_"):
                continue
            check = "%s.%s" % (_path, key)
            if check in _hide or key in hidden:
                continue
            if check in show or key in default:
                ret_data[key] = getattr(self, key)

        for key in relationships:
            if key.startswith("_"):
                continue
            check = "%s.%s" % (_path, key)
            if check in _hide or key in hidden:
                continue
            if check in show or key in default:
                _hide.append(check)
                is_list = self.__mapper__.relationships[key].uselist
                if is_list:
                    items = getattr(self, key)
                    if self.__mapper__.relationships[key].query_class is not None:
                        if hasattr(items, "all"):
                            items = items.all()
                    ret_data[key] = []
                    for item in items:
                        ret_data[key].append(
                            item.to_dict(
                                show=list(show),
                                _hide=list(_hide),
                                _path=("%s.%s" % (_path, key.lower())),
                            )
                        )
                else:
                    if (
                        self.__mapper__.relationships[key].query_class is not None
                        or self.__mapper__.relationships[key].instrument_class
                        is not None
                    ):
                        item = getattr(self, key)
                        if item is not None:
                            ret_data[key] = item.to_dict(
                                show=list(show),
                                _hide=list(_hide),
                                _path=("%s.%s" % (_path, key.lower())),
                            )
                        else:
                            ret_data[key] = None
                    else:
                        ret_data[key] = getattr(self, key)

        for key in list(set(properties) - set(columns) - set(relationships)):
            if key.startswith("_"):
                continue
            if not hasattr(self.__class__, key):
                continue
            attr = getattr(self.__class__, key)
            if not (isinstance(attr, property) or isinstance(attr, QueryableAttribute)):
                continue
            check = "%s.%s" % (_path, key)
            if check in _hide or key in hidden:
                continue
            if check in show or key in default:
                val = getattr(self, key)
                if hasattr(val, "to_dict"):
                    ret_data[key] = val.to_dict(
                        show=list(show),
                        _hide=list(_hide),
                        _path=("%s.%s" % (_path, key.lower())),
                    )
                else:
                    try:
                        ret_data[key] = json.loads(json.dumps(val))
                    except:
                        pass

        return ret_data

    def __repr__(self):
        output_format = '{}: {} - {}'
        return output_format.format(self.uuid, self.time, self.name)

class DBCreateEvent(Resource):
    def post(self):
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
        print(repr(json.dumps(str(args['body']))))
        status = add_event_to_db(new_event)
        if not status:
            return {'Error': 'Could not add event to database'}, 400
        return {'Success': 'New event added with id {}'.format(args['uuid'])}, 201

class DBQuery(Resource):
    def get(self):
        # Get most recent query
        try:
            queries = [Event.query.filter_by(name='Get interface status').order_by(Event.time.desc()).first()]
        except OperationalError:
            return {'Error': 'Database is currently empty'}, 400
        output = []
        for query in queries:
            query_serialised = query.to_dict()
            query_serialised['body'] = ast.literal_eval(query_serialised['body'])
            output.append(query_serialised)
        return output, 200

class DBGetEvent(Resource):
    def get(self):
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        if start_time is None:
            return {'Error': 'start_time has not been defined'}, 400
        if end_time is None:
            return {'Error': 'end_time has not been defined'}, 400

        queries = Event.query.filter(Event.time.between(start_time, end_time)).all()
        if not queries:
            return {'Error': 'Bad request'}, 400
        output = []
        for query in queries:
            query_serialised = query.to_dict()
            query_serialised['body'] = ast.literal_eval(query_serialised['body'])
            output.append(query_serialised)
        return output, 200


def db_init(name):
    files = glob('*')
    if db_name not in files:
        print('Creating {}'.format(name))
        db.create_all()

def create_test_event(uuid):
    test_event = Event(uuid=uuid,
                       time='2019-02-16 12:29:15.451744',
                       name='Get interface status',
                       type='CLI',
                       priority='Critical',
                       body='{"key": "value"}')
    add_event_to_db(test_event)

def add_event_to_db(event):
    try:
        db.session.add(event)
        db.session.commit()
    except IntegrityError:
        print('uuid already in database... ignoring')
        db.session.rollback()
        return False
    else:
        print('Sucessfully added {}'.format(event.uuid))
    return True

api.add_resource(DBQuery, '/get_interface_status')
api.add_resource(DBCreateEvent, '/create_event')
api.add_resource(DBGetEvent, '/get_events')

if __name__ == '__main__':
    db_name = 'core.db'
    db_init(db_name)
    app.run(debug=True)