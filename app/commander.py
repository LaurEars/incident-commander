import re

import rethinkdb as r
from repool import ConnectionPool
from rethinkdb.errors import RqlRuntimeError, RqlDriverError

from app.incident import Incident
from templates.responses import (CREATE_INCIDENT_FAILED, SET, GET, GET_LIST)


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
            return self.parse_commands(commands, channel=message['channel'])
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

    def parse_commands(self, commands, channel):
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
            return self.set_field(channel, *set_match.groups())

        get_match = re.match(r'get[ -]([A-Za-z_]+)\s*(.*)', commands, flags=re.I)
        if get_match:
            return self.get_field(channel, get_match.groups()[0])

        add_match = re.match(r'add[ -]([A-Za-z_]+)\s*(.*)', commands, flags=re.I)
        if add_match:
            return self.add_field(channel, *add_match.groups())

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

    def set_field(self, channel, field, value):
        r.table('incidents')\
            .filter({'slack_channel': channel})\
            .update({field: value})\
            .run(self.rdb)
        return SET.render(field=field, value=value)

    def get_field(self, channel, field):
        document = r.table('incidents')\
            .filter({'slack_channel': channel})\
            .run(self.rdb)
        val = document.next().get(field)

        # Use the list template if value is a list, else just return regularly
        if isinstance(val, list):
            return GET_LIST.render(field=field, value=val)
        return GET.render(field=field, value=val)

    def add_field(self, channel, field, value):
        d = r.table('incidents').filter({'slack_channel': channel}).run(self.rdb)
        d = d.next()
        r.table('incidents').filter({'slack_channel': channel}).update({
            field: r.row[field].append(value)
        }).run(self.rdb)

        return SET.render(field=field, value=value)

    # Periodic update functions
    def nag(self):
        self.pre_message()
        response = []
        incidents = r.table('incidents').run(self.rdb)
        for incident in incidents:
            channel = incident.get('slack_channel')
            message = ""
            for key in incident:
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
