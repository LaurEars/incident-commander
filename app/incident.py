import datetime
import json
import rethinkdb as r
import app.channels as channels
from templates.responses import NEW_CHANNEL_MESSAGE, SUMMARY

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
        self.leader = None
        self.steps = []
        self.symptom = []
        self.comment = []
        self.config = None

    @staticmethod
    def create_new_incident(app_name, config):
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
        incident.steps = []
        incident.leader = None
        incident.config = config
        # todo: add rest of attributes from planning session
        # todo: needs some database saving stuff
        return incident

    @staticmethod
    def get_incident_by_channel(db_conn, slack_channel):
        result = r.table('incidents')\
            .filter({'slack_channel': slack_channel})\
            .run(db_conn).next()
        incident = Incident()
        incident.start_date = result.get('start_date')
        incident.resolved_date = result.get('resolved_date')
        incident.status = result.get('status')
        incident.name = result.get('name')
        incident.app = result.get('app')
        incident.severity = result.get('severity')
        incident.slack_channel = result.get('slack_channel')
        incident.description = result.get('description')
        incident.steps = result.get('steps')
        incident.symptom = result.get('symptom')
        incident.comment = result.get('comment')
        incident.data = result
        return incident

    def add_task(self, task):
        self.steps.append(task)
        # todo: needs some database saving stuff

    def create_channel(self):
        """Ensures that a channel is created for the incident"""
        # todo: create channel in slack - hopefully it doesn't already exist
        try:
            resp = channels.create(self.name, self.config)
            self.slack_channel = resp['channel']['id']
            self.name = resp['channel']['name']
            channels.join(self.slack_channel, self.config)
            channels.post(self.slack_channel, self.config,
                          NEW_CHANNEL_MESSAGE.render())

        except ValueError as err:
            print(err)


    def summarize(self):
        """Returns a summary of the incident"""
        return SUMMARY.render(
            name=self.name,
            status=self.status,
            severity=self.severity,
            start_date=self.start_date,
            resolved_date=self.resolved_date,
            description=self.description,
            steps=self.steps,
            symptom=self.symptom
        )

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
                     'leader': self.leader,
                     'steps': self.steps,
                     'start_date': r.expr(self.start_date),
                     'resolved_date': self.resolved_date},
                    conflict="update")\
            .run(db_conn)

    def _format_title_for_field(self, field):
        titles = {
            'status': 'Current Status',
            'symptom': 'Symptoms',
            'hypothesis': 'Hypotheses under investigation',
            'start_date': 'First reported',
            'steps': 'Steps taken',
            'comment': 'Comments'
        }
        if field in titles:
            return titles[field]
        else:
            return field.capitalize()


    def _format_value_for_field(self, field_value):
        def _get_text(f):
            if isinstance(f, str):
                return f
            elif f['removed']:
                return '• ~{}~  (<@{}>)'.format(f['text'], f['user'])
            else:
                return '• {} (<@{}>)'.format(f['text'], f['user'])

        if isinstance(field_value, list):
            return '\n'.join([_get_text(i) for i in field_value])
        elif isinstance(field_value, datetime.datetime):
            return field_value.strftime("%Y-%m-%d %I:%M:%S")
        return field_value

    def post_summary(self, config):
        short_fields = [
            'status', 'severity', 'leader', 'start_date'
        ]
        formatted_fields = {}
        for field_name, field_value in self.data.items():
            formatted_fields[field_name] = {
                'title': self._format_title_for_field(field_name),
                'value': self._format_value_for_field(field_value),
                'short': field_name in short_fields
            }


        attachments = [
            {
                'mrkdwn_in': ['text', 'fields'],
                'color': 'danger',
                'title': self.name,
                'text': self.description,
                'fields': [i for i in [
                    formatted_fields.get('status'),
                    formatted_fields.get('severity'),
                    formatted_fields.get('leader'),
                    formatted_fields.get('start_date')
                ] if i != None]
            },
            {
                'mrkdwn_in': ['text', 'fields'],
                'color': 'warning',
                'title': 'Investigation',
                'fields': [i for i in [
                    formatted_fields.get('symptoms'),
                    formatted_fields.get('hypothesis'),
                    formatted_fields.get('comment'),
                    formatted_fields.get('steps')
                ] if i != None]
            }
        ]
        print(attachments)
        channels.post(self.slack_channel, config=config, message='*Incident Summary*', attachments=json.dumps(attachments))