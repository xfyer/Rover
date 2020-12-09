#!/usr/bin/python

import json
import logging
from typing import Optional, Any, Reversible
from json.decoder import JSONDecodeError
from os import path

import twitter
from doltpy.core.system_helpers import get_logger
from twitter import TwitterError

from rover import commands, config
from config import config as main_config


class Rover:
    def __init__(self):
        self.logger: logging.Logger = get_logger(__name__)
        self.INFO_QUIET: int = main_config.INFO_QUIET
        self.VERBOSE: int = main_config.VERBOSE
        self.status_file: str = config.STATUS_FILE_PATH
        self.credentials_file: str = config.CREDENTIALS_FILE_PATH

        # TODO: Figure Out How To Automatically Determine This
        self.user_id: int = config.TWITTER_USER_ID
        self.user_name: str = config.TWITTER_USER_HANDLE

        # Debugging Paths
        self.logger.info("Working Directory: {working_directory}".format(working_directory=config.WORKING_DIRECTORY))

        # Setup For Twitter API
        with open(self.credentials_file, "r") as file:
            self.__credentials: dict = json.load(file)

    def look_for_tweets(self):
        # self.save_status_to_file(status_id=1335821481557831679)  # For Debugging Bot

        self.logger.log(self.INFO_QUIET, "Checking For New Tweets")
        last_replied_status = self.read_status_from_file()
        replied_to_status = self.process_tweet(latest_status=last_replied_status)

        if replied_to_status is not None:
            self.save_status_to_file(replied_to_status)

    def process_tweet(self, latest_status: int = None) -> int:
        api = twitter.Api(consumer_key=self.__credentials['consumer']['key'],
                          consumer_secret=self.__credentials['consumer']['secret'],
                          access_token_key=self.__credentials['token']['key'],
                          access_token_secret=self.__credentials['token']['secret'],
                          sleep_on_rate_limit=True,
                          tweet_mode="extended")

        mentions: Reversible[json] = api.GetMentions(since_id=latest_status)
        # mentions: Reversible[json] = api.GetStatuses(status_ids=[1334461310734659584, 1334465300243345408, 1334466433368137729, 1335104236129046528, 1335109553088831489, 1335110267932438528])  # For Debugging Bot
        # mentions = api.GetStatuses(status_ids=[1335104236129046528])

        latest_status = None
        for mention in reversed(mentions):
            # Don't Respond To Own Tweets (870156302298873856 is user id for @DigitalRoverDog)
            if mention.user.id == self.user_id:
                continue

            # To Prevent Implicit Replying (So the bot only replies to explicit requests)
            if not self.is_explicitly_mentioned(mention=mention):
                continue

            self.logger.log(self.INFO_QUIET,
                            "Responding To Tweet From @{user}: {text}".format(user=mention.user.screen_name,
                                                                              text=mention.full_text))

            try:
                commands.process_command(api=api, status=mention,
                                         logger_param=self.logger,
                                         info_level=self.INFO_QUIET,
                                         verbose_level=self.VERBOSE)

            except TwitterError as e:
                # To Deal With That Duplicate Status Error - [{'code': 187, 'message': 'Status is a duplicate.'}]
                error: json = e.message[0]
                # TODO FIX: TypeError: string indices must be integers FOR "Text must be less than or equal to CHARACTER_LIMIT characters."
                self.logger.error("Twitter Error (Code {code}): {error_message}".format(code=error["code"],
                                                                                        error_message=error["message"]))

            latest_status = mention.id

        return latest_status

    def is_explicitly_mentioned(self, mention: json) -> bool:
        # If the mention shows up more than once, return true. Twitter adds one implicit reply when replying to a user,
        # but if more than one mention exists, then it's a guaranteed explicit mention.
        if mention.full_text.startswith(self.user_name + " ") and mention.full_text.count(self.user_name) == 1:
            # If Not A Reply, Accept (Since It Cannot Be An Implicit Mention Added By Twitter)
            if mention.in_reply_to_status_id is None:
                return True

            # 1334465300243345408 should pass, 1335110267932438528 should fail
            # Pass means that the method returns true
            # AFAICT, there's no way to filter between these two test cases atm

            self.logger.log(self.VERBOSE,
                            "Own Name: {own_name}, Own ID: {own_id}".format(own_name=self.user_name,
                                                                            own_id=self.user_id))
            self.logger.debug("Tweet with ID {id} Failed to Pass Filter: {json}".format(id=mention.id, json=mention))
            return False

        return True

    def save_status_to_file(self, status_id: int):
        file_contents = {
            "last_status": status_id
        }

        f = open(self.status_file, "w")
        f.write(json.dumps(file_contents))
        f.close()

    def read_status_from_file(self) -> Optional[Any]:
        if not path.exists(self.status_file):
            return None

        f = open(self.status_file, "r")
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
