#!/usr/bin/python

import twitter


def process_command(status: twitter.models.Status) -> str:
    return "@{user} Hello {name}".format(name=status.user.name, user=status.user.screen_name)