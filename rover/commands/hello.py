#!/usr/bin/python

import twitter

from rover import config


def say_hello(api: twitter.Api, status: twitter.models.Status):
    new_status = "@{user} Hello {name}".format(name=status.user.name, user=status.user.screen_name)

    if config.REPLY:
        api.PostUpdate(in_reply_to_status_id=status.id, status=new_status)
