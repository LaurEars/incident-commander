# incident commander

Slack bot to manage incidents

## Setup

On OSX run the following:

```bash
pyenv install 3.5.1
pyenv virtualenv 3.5.1 commander
pyenv activate commander

brew install rethinkdb

pip install -r requirements.txt

```

## Configuration

Put the following into `rtmbot.conf`:

```
DEBUG: False

SLACK_TOKEN: "xoxb-111111111111-2222222222222222222"
APP_TOKEN: "xoxp-1111111111-2222222222-3333333333-444444444"

db_host: "localhost"
db_port: 28015
db_name: "commander"

name: "commander"
id: "U1EHRETL3"

```

## Development

To run `autopep8` on your code:

```
make pep8
```

## Running the Bot

In one terminal, run:
```
rethinkdb
```

In another terminal, run:
```
python rtmbot.py
```

## Running the changefeed workers
