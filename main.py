#!/usr/bin/python

import argparse
# import pandas as pd
import logging
from json.decoder import JSONDecodeError
from os import path

import twitter
import json

# Custom Log Levels
from doltpy.core import system_helpers
from doltpy.core.system_helpers import get_logger

# Commands
from commands import process_command

VERBOSE = logging.DEBUG - 1
logging.addLevelName(VERBOSE, "VERBOSE")

# Dolt Logger - logging.getLogger(__name__)
logger = get_logger(__name__)

# Argument Parser Setup
parser = argparse.ArgumentParser(description='Arguments For Tweet Searcher')
parser.add_argument("-log", "--log", help="Set Log Level (Defaults to WARNING)",
                    dest='logLevel',
                    default='WARNING',
                    type=str.upper,
                    choices=['VERBOSE', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])


def main(arguments: argparse.Namespace):
    # Set Logging Level
    logging.Logger.setLevel(system_helpers.logger, arguments.logLevel)  # DoltPy's Log Level
    logger.setLevel(arguments.logLevel)  # This Script's Log Level

    # Setup For Twitter API
    with open("credentials.json", "r") as file:
        credentials = json.load(file)

    last_replied_status = read_status_from_file()
    replied_to_status = run_search(credentials=credentials, latest_status=last_replied_status)

    if replied_to_status is not None:
        save_status_to_file(replied_to_status)


def save_status_to_file(status_id: int):
    file_contents = {
        "last_status": status_id
    }

    f = open("latest_status.json", "w")
    f.write(json.dumps(file_contents))
    f.close()


def read_status_from_file() -> int:
    file = "latest_status.json"
    if not path.exists(file):
        return None

    f = open(file, "r")
    filecontents = f.read()
    f.close()

    # {"last_status": 1333984649056546816}
    try:
        decoded = json.loads(filecontents)

        if 'last_status' not in decoded:
            return None
    except JSONDecodeError:
        return None

    return decoded['last_status']


def run_search(credentials: json, latest_status: int = None) -> int:
    api = twitter.Api(consumer_key=credentials['consumer']['key'],
                      consumer_secret=credentials['consumer']['secret'],
                      access_token_key=credentials['token']['key'],
                      access_token_secret=credentials['token']['secret'],
                      sleep_on_rate_limit=True)

    mentions = api.GetMentions(since_id=latest_status)

    latest_status = None
    for mention in reversed(mentions):
        # Don't Respond To Own Tweets (870156302298873856 is user id for @DigitalRoverDog)
        if mention.user.id == 870156302298873856:
            continue

        new_status = process_command(status=mention)
        logger.warning(new_status)

        api.PostUpdate(in_reply_to_status_id=mention.id, status=new_status)
        latest_status = mention.id

    return latest_status


if __name__ == '__main__':
    # This is to get DoltPy's Logger To Shut Up When Running `this_script.py -h`
    logging.Logger.setLevel(system_helpers.logger, logging.CRITICAL)

    args = parser.parse_args()
    main(args)
