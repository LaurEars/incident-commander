import yaml

from app.commander import Commander

crontable = []
outputs = []

config = yaml.load(open('rtmbot.conf', 'r'))

commander = Commander(config)


def process_message(data):
    response = commander.process_message(data)
    if response:
        outputs.append([data['channel'], response])
