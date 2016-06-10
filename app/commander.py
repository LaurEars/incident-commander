import re

import rethinkdb as r
from repool import ConnectionPool
from rethinkdb.errors import RqlRuntimeError, RqlDriverError

from app.incident import Incident
from templates.responses import (CREATE_INCIDENT_FAILED, SET, GET, GET_LIST, NAG)

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

class CommanderBase:
    """
    Incident commander main class
    """

    def __init__(self, config):
        self.config = config
        print(self.config)

        self.name = self.config['name']
        self.id = self.config['id']
        self.db_name = self.config['db_name']

        self.rdb = r.connect(
            host=self.config['db_host'],
            port=self.config['db_port']
        )

        try:
            r.db_create(self.db_name).run(self.rdb)
            r.db(self.db_name)\
                .table_create('incidents', primary_key='slack_channel')\
                .run(self.rdb)
            print('Database setup completed.')
        except RqlRuntimeError:
            print('App database already exists.')

        self.rdb.close()

        self.pool = ConnectionPool(
            host=self.config['db_host'],
            port=self.config['db_port'],
            db=self.db_name
        )


    def pre_message(self):
        try:
            self.rdb = self.pool.acquire()
        except RqlDriverError:
            print("Could not connect to db")

    def post_message(self):
        self.pool.release(self.rdb)


    def process_message(self, message):
        self.pre_message()
        return_val = self.parse_message(message)
        self.post_message()
        return return_val

    def parse_message(self, message):
        if not self.valid_message(message):
            return ""

        stripped_message = message['text'].strip()
        name_match = re.match(r'<@?{}>:?\s*(.*)'.format(self.id),
                              stripped_message,
                              flags=re.IGNORECASE)
        if name_match:
            commands = name_match.groups()[0]
            return self.parse_commands(commands, channel=message['channel'], user=message['user'])
        if message['channel'].startswith('D'):
            return self.parse_commands(stripped_message,
                                       channel=message['channel'])

    def valid_message(self, message):
        return message.get('user') != self.id

    def parse_commands(self, commands, channel):
        return NotImplementedError


class Commander(CommanderBase):
    def __init__(self, *args, **kwargs):
        super(Commander, self).__init__(*args, **kwargs)

    def parse_commands(self, commands, channel, user):
        print(user)
        # Run down a big old list of short-circuiting ifs to determine
        # which command was called
        create_incident = re.match(r'create[ -]incident\s*(.*)',
                                   commands,
                                   flags=re.I)
        if create_incident:
            # begin workflow for creating incident
            return self.create_incident(create_incident.groups()[0])

        set_match = re.match(r'set[ -]([A-Za-z_]+)\s*(.*)', commands, flags=re.I)
        if set_match:
            print(set_match.groups())
            return self.set_field(channel, user, set_match.groups()[0], set_match.groups()[1])

        get_match = re.match(r'get[ -]([A-Za-z_]+)\s*(.*)', commands, flags=re.I)
        if get_match:
            return self.get_field(channel, get_match.groups()[0])

        add_match = re.match(r'add[ -]([A-Za-z_]+)\s*(.*)', commands, flags=re.I)
        if add_match:
            return self.add_field(channel, user, add_match.groups()[0], add_match.groups()[1])

        remove_match = re.match(r'remove[ -]([A-Za-z_]+)\s+([1-9]\d*)', commands, flags=re.I)
        if remove_match:
            return self.remove_field(channel, *remove_match.groups())

        return 'no match for this command'

    def create_incident(self, app_name):
        # catches "for app-name" or "app-name"
        current_app_name = re.match(r'(?:for\s+)?(.*)', app_name)
        if not current_app_name:
            return CREATE_INCIDENT_FAILED.render()
        incident = Incident.create_new_incident(current_app_name.groups()[0], self.config)
        incident.create_channel()
        incident.save(self.rdb)
        return 'Created incident!: <#{}|{}>'.format(incident.slack_channel, incident.name)

    def set_field(self, channel, user, field, value):
        if field in LIST_FIELDS:
            return self.add_field(channel, user, field, value)

        incident = Incident.get_incident_by_channel(self.rdb, channel)
        try:
            incident[field] = value
            incident.save(self.rdb)
        except KeyError:
            return "{} is not a field that exists on an incident".format(field)
        return SET.render(field=field, value=value)

    def get_field(self, channel, field):
        incident = Incident.get_incident_by_channel(self.rdb, channel)
        val = incident.get(field)

        # Use the list template if value is a list, else just return regularly
        if isinstance(val, list):
            return GET_LIST.render(field=field, value=val)
        return GET.render(field=field, value=val)

    def add_field(self, channel, user, field, value):
        if field not in LIST_FIELDS:
            return '`add` commands can only be used with one of the following: {}'.format(', '.join(LIST_FIELDS))

        d = r.table('incidents').filter({'slack_channel': channel}).run(self.rdb)
        d = d.next()
        r.table('incidents').filter({'slack_channel': channel}).update({
            field: r.row[field].default([]).append({
                'ts': r.now(),
                'user': user,
                'text': value,
                'removed': False
            })
        }, return_changes=True).run(self.rdb)

        return self.get_field(channel, field)

    def remove_field(self, channel, field, display_index):
        if field not in LIST_FIELDS:
            return '`remove` commands can only be used with one of the following: {}'.format(', '.join(LIST_FIELDS))

        # lists are numbered starting from 1, not 0, so subract 1 for the real index
        index = int(display_index)
        if index > 0:
            index = index - 1
        else:
            return 'Items number must be 1 or greater'

        r.table('incidents').filter({'slack_channel': channel}).update({
            field: r.row[field].change_at(index,
                r.row[field][index].merge({
                    'removed': True
                })
            )
        }).run(self.rdb)

        return self.get_field(channel, field)

    # Periodic update functions
    def nag(self):
        self.pre_message()
        response = []
        incidents = r.table('incidents').run(self.rdb)
        for incident in incidents:
            channel = incident.get('slack_channel')
            message = ""
            for key in CRITICAL_FIELDS:
                if incident.get(key) is None:
                    message = "{}\n{}".format(message, NAG.render(key=key))
            response.append([channel, message])
        self.post_message()
        return response

    def update(self):
        self.pre_message()
        response = []
        incidents = r.table('incidents').run(self.rdb)
        for incident in incidents:
            channel = incident.get('slack_channel') # This will just return to the incident channel, thoughts?
            message = "" # This should be the summary!
            response.append([channel, message])
        self.post_message()
        return response
