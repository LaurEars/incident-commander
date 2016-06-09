import re

import rethinkdb as r
from repool import ConnectionPool
from rethinkdb.errors import RqlRuntimeError, RqlDriverError

from app.incident import Incident
from templates.responses import CREATE_INCIDENT_FAILED


class Commander:
    """
    Incident commander main class
    """

    def __init__(self, config):
        self.config = config
        print(self.config)

        self.name = self.config['name']
        self.id = self.config['id']

        self.rdb = r.connect(
            host=self.config['db_host'],
            port=self.config['db_port']
        )

        try:
            r.db_create("commander").run(self.rdb)
            r.db("commander").table_create('incidents').run(self.rdb)
            print('Database setup completed.')
        except RqlRuntimeError:
            print('App database already exists.')

        self.rdb.close()

        self.pool = ConnectionPool(
            host=self.config['db_host'],
            port=self.config['db_port'],
            db="commander"
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
        return_val = self.parse_message(message['text'])
        self.post_message()
        return return_val

    def parse_message(self, message):
        stripped_message = message.strip()
        name_match = re.match(r'<@?{}>:?\s*(.*)'.format(self.id),
                              stripped_message,
                              flags=re.IGNORECASE)
        if name_match:
            commands = name_match.groups()[0]
            # parse message as incident commander message
            task_match = re.match(r'add task\s*(.*)', commands, flags=re.I)
            if task_match:
                return self.add_task(task_match.groups()[0])

            create_incident = re.match(r'create[ -]incident\s*(.*)',
                                       commands,
                                       flags=re.I)
            if create_incident:
                # begin workflow for creating incident
                return self.create_incident(create_incident.groups()[0])
            return 'no match for this command'

    def add_task(self, task):
        # todo: add task to task list
        print(task)
        return 'Added task to list!'

    def create_incident(self, app_name):
        # catches "for app-name" or "app-name"
        current_app_name = re.match(r'(?:for ?)(.*)', app_name)
        if not current_app_name:
            return CREATE_INCIDENT_FAILED.render()
        incident = Incident(app_name)
        incident.create_channel()
        # todo: say stuff in channel
        # todo: push empty document to database
        return 'Created incident!: {}'.format(incident.name)
