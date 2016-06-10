import datetime
import rethinkdb as r


class Incident:
    def __init__(self):
        self.start_date = None
        self.resolved_date = None
        self.status = None
        self.name = None
        self.app = None
        self.severity = None
        self.slack_channel = None
        self.description = None
        self.tasks = []

    @staticmethod
    def create_new_incident(app_name):
        incident = Incident()
        incident.start_date = datetime.datetime.now(r.make_timezone('-07:00'))
        incident.resolved_date = None
        incident.status = 'Identified'  # should be an enum-type thing
        incident.name = "{today_format}-{app_name}"\
            .format(today_format=incident.start_date.strftime("%Y-%m-%d"),
                    app_name=app_name)
        incident.app = app_name
        incident.severity = None  # should be another enum-like thing
        incident.slack_channel = None
        incident.description = None
        incident.tasks = []
        # todo: add rest of attributes from planning session
        # todo: needs some database saving stuff
        return incident

    @staticmethod
    def get_incident_by_channel(db_conn, slack_channel):
        result = r.table('incidents')\
            .filter({'slack_channel': slack_channel})\
            .run(db_conn).next()
        incident = Incident()
        incident.start_date = result['start_date']
        incident.resolved_date = result['resolved_date']
        incident.status = result['status']
        incident.name = result['name']
        incident.app = result['app']
        incident.severity = result['severity']
        incident.slack_channel = result['slack_channel']
        incident.description = result['description']
        incident.tasks = result['tasks']
        return incident

    def add_task(self, task):
        self.tasks.append(task)
        # todo: needs some database saving stuff

    def create_channel(self):
        """Ensures that a channel is created for the incident"""
        # todo: create channel in slack - hopefully it doesn't already exist
        self.slack_channel = None
        # todo: update in db

    @staticmethod
    def get_incident(db_conn, id):
        return r.table('incidents').get(id).run(db_conn)

    def save(self, db_conn):
        r.table('incidents')\
            .insert({'name': self.name,
                     'status': self.status,
                     'app': self.app,
                     'severity': self.severity,
                     'slack_channel': self.slack_channel,
                     'description': self.description,
                     'tasks': self.tasks,
                     'start_date': r.expr(self.start_date),
                     'resolved_date': self.resolved_date},
                    conflict="update")\
            .run(db_conn)
