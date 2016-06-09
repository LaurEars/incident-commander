import re

import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError, RqlDriverError


class Commander:
    """
    Incident commander main class
    """

    def __init__(self, config):
        self.config = config
        print(self.config)
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

    def process_message(self, message):
        return self.parse_message(message['text'])

    def parse_message(self, message):
        stripped_message = message.strip()
        commander_match = re.match(r'commander\s*(.*)',
                                   stripped_message,
                                   flags=re.IGNORECASE)
        if commander_match:
            # parse message as incident commander message
            task_match = re.match(r'add task\s*(.*)',
                                  commander_match.groups()[0],
                                  flags=re.I)
            if task_match:
                return self.add_task(task_match.groups()[0])
            return 'no match for this command'

    def add_task(self, task):
        # add task to task list
        print(task)
        return 'Added task to list!'
