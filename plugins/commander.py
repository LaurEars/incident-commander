import yaml

from app.commander import Commander

crontable = []
outputs = []

# Instantiate commader!
config = yaml.load(open('rtmbot.conf', 'r'))
commander = Commander(config)

# main message processing


def process_message(data):
    if config["DEBUG"]:
        print(data)

    response = commander.process_message(data)
    if response:
        outputs.append([data['channel'], response])

# crontable functions


def periodic_nag():
    for channel, message in commander.nag():
        outputs.append([channel, message])


def periodic_updates():
    for channel, message in commander.update():
        outputs.append([channel, message])


# Add function to crontable
crontable.append([15, "periodic_nag"])
crontable.append([60, "periodic_updates"])
