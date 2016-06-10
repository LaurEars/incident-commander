import datetime
import json
import requests
import rethinkdb as r
from rethinkdb.errors import ReqlCursorEmpty
import app.channels as channels
from templates.responses import NEW_CHANNEL_MESSAGE, SUMMARY


LIST_FIELDS = [
    'symptom',
    'hypothesis',
    'comments',
    'steps',
    'tasks'
]
CRITICAL_FIELDS = [
    'description',
    'status',
    'severity',
    'leader'
]


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
        self.hypothesis = []
        self.config = None
        self.resolved = False

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
        incident.resolved = False
        # todo: add rest of attributes from planning session
        # todo: needs some database saving stuff
        return incident

    @staticmethod
    def get_incident_by_channel(db_conn, slack_channel):
        result = r.table('incidents')\
            .filter({'slack_channel': slack_channel})\
            .run(db_conn)

        try:
            result = result.next()
        except ReqlCursorEmpty:
            i = Incident()
            i.name = "Cant Find Incident"
            i.data = {}
            return i

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
        incident.hypothesis = result.get('hypothesis')
        incident.data = result
        incident.leader = result.get('leader')
        return incident

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

            # Hit the lights!
            requests.get('http://172.29.30.161/events/sev-1-start')

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
                     'symptom': self.symptom,
                     'comment': self.comment,
                     'hypothesis': self.hypothesis,
                     'start_date': r.expr(self.start_date),
                     'resolved_date': self.resolved_date},
                    conflict="update")\
            .run(db_conn)

    @staticmethod
    def _format_title_for_field(field):
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

    @staticmethod
    def _format_value_for_field(field_value):
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
                'title': Incident._format_title_for_field(field_name),
                'value': Incident._format_value_for_field(field_value),
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
                ] if i is not None]
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
                ] if i is not None]
            }
        ]
        print(attachments)
        channels.post(self.slack_channel, config=config,
                      message='*Incident Summary*', attachments=json.dumps(attachments))

    def resolve(self, channel, db_conn):
        r.table('incidents').get(channel)\
            .update({'resolved': True}).run(db_conn)
        # Hit the lights!
        requests.get('http://172.29.30.161/events/sev-1-end')
        return "Incident Resolved!"
