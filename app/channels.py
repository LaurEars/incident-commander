from slackclient import SlackClient

def createChannel(name, config):
    sc = SlackClient(config['APP_TOKEN'])
    resp = sc.api_call('channels.create', name=name)
    created = resp['ok']
    if created:
        return resp
    else:
        raise ValueError('Failed creating channel {}. Error was {}'.format(name, resp['error']))