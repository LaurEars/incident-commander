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

```
python rtmbot.py
```

## Running the changefeed workers
