import datetime
import rethinkdb as r

class Incident:
    def __init__(self, app_name):
        self.start_date = datetime.date.today()
        self.resolved_date = None
        self.status = 'Identified'  # should be an enum-type thing
        self.name = "{today_format}-{app_name}"\
            .format(today_format=self.start_date.strftime("%Y-%m-%d"),
                    app_name=app_name)
        self.app = app_name
        self.severity = None  # should be another enum-like thing
        self.slack_channel = None
        self.description = None
        self.tasks = []
        # todo: add rest of attributes from planning session
        # todo: needs some database saving stuff

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
