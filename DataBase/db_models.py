from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Event(db.Model):
    """Event model for the database"""
    __tablename__ = 'event'
    uuid = db.Column(db.String(37), unique=True, primary_key=True, nullable=False)
    time = db.Column(db.String(27), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    priority = db.Column(db.String(20), nullable=True)
    body = db.Column(db.String(100000), nullable=True)

    def __repr__(self):
        output_format = '{}: {} - {}'
        return output_format.format(self.uuid, self.time, self.name)


class Execution(db.Model):
    """Execution model for the database"""
    __tablename__ = 'execution'
    uuid = db.Column(db.String(37), unique=True, primary_key=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    binded_events = db.Column(db.String(1000), nullable=False)
    time = db.Column(db.String(27), nullable=False)
    commands = db.Column(db.String(100000), nullable=True)
    status = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        output_format = '{}: {} - {}'
        return output_format.format(self.uuid, self.time, self.name)
