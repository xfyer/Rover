#!/usr/bin/python

import argparse
import logging
from json.decoder import JSONDecodeError
from os import path
from typing import Reversible, Optional, Any

import twitter
import json
import time

# Custom Log Levels
from doltpy.core import system_helpers
from doltpy.core.system_helpers import get_logger

# Commands
from twitter import TwitterError

from commands import process_command

VERBOSE = logging.DEBUG - 1
logging.addLevelName(VERBOSE, "VERBOSE")

INFO_QUIET = logging.INFO + 1
logging.addLevelName(INFO_QUIET, "INFO_QUIET")

# Dolt Logger - logging.getLogger(__name__)
logger: logging.Logger = get_logger(__name__)

# Argument Parser Setup
parser = argparse.ArgumentParser(description='Arguments For Tweet Searcher')
parser.add_argument("-log", "--log", help="Set Log Level (Defaults to WARNING)",
                    dest='logLevel',
                    default='INFO_QUIET',
                    type=str.upper,
                    choices=['VERBOSE', 'DEBUG', 'INFO', 'INFO_QUIET', 'WARNING', 'ERROR', 'CRITICAL'])

parser.add_argument("-wait", "--wait", help="Set Delay Before Checking For New Tweets In Minutes",
                    dest='wait',
                    default=1,
                    type=int)


def main(arguments: argparse.Namespace):
    # Set Logging Level
    logging.Logger.setLevel(system_helpers.logger, arguments.logLevel)  # DoltPy's Log Level
    logger.setLevel(arguments.logLevel)  # This Script's Log Level

    # Setup For Twitter API
    with open("credentials.json", "r") as file:
        credentials = json.load(file)

    wait_time: int = arguments.wait * 60
    wait_unit: str = "Minute" if wait_time == 60 else "Minutes"  # Because I Keep Forgetting What This Is Called, It's Called A Ternary Operator
    while 1:
        logger.log(INFO_QUIET, "Checking For New Tweets")
        last_replied_status = read_status_from_file()
        replied_to_status = process_tweet(credentials=credentials, latest_status=last_replied_status)

        if replied_to_status is not None:
            save_status_to_file(replied_to_status)

        logger.log(INFO_QUIET, "Waiting For {time} {unit} Before Checking For New Tweets".format(time=arguments.wait, unit=wait_unit))
        time.sleep(wait_time)


def save_status_to_file(status_id: int):
    file_contents = {
        "last_status": status_id
    }

    f = open("latest_status.json", "w")
    f.write(json.dumps(file_contents))
    f.close()


def read_status_from_file() -> Optional[Any]:
    file = "latest_status.json"
    if not path.exists(file):
        return None

    f = open(file, "r")
    file_contents = f.read()
    f.close()

    # {"last_status": 1333984649056546816}
    try:
        decoded = json.loads(file_contents)

        if 'last_status' not in decoded:
            return None
    except JSONDecodeError:
        return None

    return decoded['last_status']


def process_tweet(credentials: json, latest_status: int = None) -> int:
    api = twitter.Api(consumer_key=credentials['consumer']['key'],
                      consumer_secret=credentials['consumer']['secret'],
                      access_token_key=credentials['token']['key'],
                      access_token_secret=credentials['token']['secret'],
                      sleep_on_rate_limit=True,
                      tweet_mode="extended")

    own_id = 870156302298873856
    own_name = "@DigitalRoverDog"

    mentions: Reversible[json] = api.GetMentions(since_id=latest_status)
    # mentions: Reversible[json] = api.GetStatuses(status_ids=[1334461310734659584, 1334465300243345408, 1334466433368137729, 1335104236129046528, 1335109553088831489, 1335110267932438528])  # For Debugging Bot
    # mentions = api.GetStatuses(status_ids=[1335104236129046528])

    latest_status = None
    for mention in reversed(mentions):
        # Don't Respond To Own Tweets (870156302298873856 is user id for @DigitalRoverDog)
        if mention.user.id == own_id:
            continue

        # To Prevent Implicit Replying (So the bot only replies to explicit requests)
        if not is_explicitly_mentioned(mention=mention, own_name=own_name, own_id=own_id):
            continue

        logger.log(INFO_QUIET, "Responding To Tweet From @{user}: {text}".format(user=mention.user.screen_name, text=mention.full_text))

        try:
            process_command(api=api, status=mention, logger_param=logger, info_level=INFO_QUIET, verbose_level=VERBOSE)
        except TwitterError as e:
            # To Deal With That Duplicate Status Error - [{'code': 187, 'message': 'Status is a duplicate.'}]
            error: json = e.message[0]
            # TODO FIX: TypeError: string indices must be integers FOR "Text must be less than or equal to CHARACTER_LIMIT characters."
            logger.error("Twitter Error (Code {code}): {error_message}".format(code=error["code"], error_message=error["message"]))

        latest_status = mention.id

    return latest_status


def is_explicitly_mentioned(mention: json, own_name: str, own_id: int = None) -> bool:
    # If the mention shows up more than once, return true. Twitter adds one implicit reply when replying to a user,
    # but if more than one mention exists, then it's a guaranteed explicit mention.
    if mention.full_text.startswith(own_name + " ") and mention.full_text.count(own_name) == 1:
        # If Not A Reply, Accept (Since It Cannot Be An Implicit Mention Added By Twitter)
        if mention.in_reply_to_status_id is None:
            return True

        # 1334465300243345408 should pass, 1335110267932438528 should fail
        # Pass means that the method returns true
        # AFAICT, there's no way to filter between these two test cases atm

        logger.log(VERBOSE, "Own Name: {own_name}, Own ID: {own_id}".format(own_name=own_name, own_id=own_id))
        logger.debug("Tweet with ID {id} Failed to Pass Filter: {json}".format(id=mention.id, json=mention))
        return False

    return True


if __name__ == '__main__':
    # This is to get DoltPy's Logger To Shut Up When Running `this_script.py -h`
    logging.Logger.setLevel(system_helpers.logger, logging.CRITICAL)

    # save_status_to_file(status_id=1335821481557831679)  # For Debugging Bot

    args = parser.parse_args()
    try:
        main(args)
    except KeyboardInterrupt:
        logger.warning("Exiting By User Request...")
        exit(0)
