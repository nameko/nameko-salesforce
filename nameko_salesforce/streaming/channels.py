from nameko_bayeux_client.channels import Subscribe as BaseSubscribe


class Subscribe(BaseSubscribe):
    """ Subscribe channel with Salesforce PushTopic Replay extension
    """

    def compose(self, channel_name, replay_id=None):
        compose = super(BaseSubscribe, self).compose
        if replay_id:
            ext = {'replay': {channel_name: replay_id}}
            return compose(subscription=channel_name, ext=ext)
        else:
            return compose(subscription=channel_name)
