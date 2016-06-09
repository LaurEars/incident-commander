from __future__ import unicode_literals
from app.commander import Commander
# don't convert to ascii in py2.7 when creating string to return

crontable = []
outputs = []

commander = Commander()


def process_message(data):

    response = commander.process_message(data)
    if response:
        outputs.append([data['channel'], response])
