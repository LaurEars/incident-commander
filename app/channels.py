from slackclient import SlackClient


def create(name, config, iteration=0):
    sc = SlackClient(config['APP_TOKEN'])
    if iteration:
        channelName = '{}-{}'.format(name, iteration)
    else:
        channelName = name
    resp = sc.api_call('channels.create', name=channelName)
    created = resp['ok']
    if created:
        return resp
    else:
        if resp['error'] == 'name_taken':
            return create(name, config, iteration + 1)
        else:
            raise ValueError('Failed creating channel {}. Error was {}'
                             .format(name, resp['error']))


def join(channel, config):
    sc = SlackClient(config['APP_TOKEN'])
    resp = sc.api_call('channels.invite', channel=channel, user=config['id'])
    joined = resp['ok']

    if not joined:
        raise ValueError('Failed to join channel {}. Error was {}'.format(
            channel, resp['error']))


def post(channel, config, message):
    sc = SlackClient(config['SLACK_TOKEN'])
    resp = sc.api_call('chat.postMessage', channel=channel,
                       text=message, unfurl_links=True)
    posted = resp['ok']
    print(resp)
