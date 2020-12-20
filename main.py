#!/usr/bin/python

import argparse
import logging
import time

# Custom Log Levels
from doltpy.core import system_helpers
from doltpy.core.system_helpers import get_logger

from config import config as main_config
from rover import Rover
from archiver import Archiver

# Dolt Logger - logging.getLogger(__name__)
from rover.server import WebServer

logger: logging.Logger = get_logger(__name__)

# Argument Parser Setup
parser = argparse.ArgumentParser(description='Arguments For Tweet Searcher')
parser.add_argument("-log", "--log", help="Set Log Level (Defaults to INFO_QUIET)",
                    dest='logLevel',
                    default='INFO_QUIET',
                    type=str.upper,
                    choices=['VERBOSE', 'DEBUG', 'INFO', 'INFO_QUIET', 'WARNING', 'ERROR', 'CRITICAL'])

parser.add_argument("-wait", "--wait", help="Set Delay Before Checking For New Tweets In Minutes (Defaults To 1 Minute)",
                    dest='wait',
                    default=1,
                    type=int)

parser.add_argument("-reply", "--reply", help="Reply to Tweets (Useful For Debugging) (Defaults To True)",
                    dest='reply',
                    default=True,
                    type=bool,
                    action=argparse.BooleanOptionalAction)

parser.add_argument("-rover", "--rover", help="Look For Tweets To Respond To (Useful For Disabling Rover Entirely) (Defaults To True)",
                    dest='rover',
                    default=True,
                    type=bool,
                    action=argparse.BooleanOptionalAction)

parser.add_argument("-archive", "--archive", help="Archives Tweets (Useful For Debugging) (Defaults To True)",
                    dest='archive',
                    default=True,
                    type=bool,
                    action=argparse.BooleanOptionalAction)

parser.add_argument("-server", "--server", help="Run Webserver (Defaults To True)",
                    dest='server',
                    default=True,
                    type=bool,
                    action=argparse.BooleanOptionalAction)

parser.add_argument("-commit", "--commit", help="Commit Tweets To Repo When Archived (Useful For Debugging) (Defaults To True)",
                    dest='commit',
                    default=True,
                    type=bool,
                    action=argparse.BooleanOptionalAction)


def main(arguments: argparse.Namespace):
    # Set Logging Level
    logging.Logger.setLevel(system_helpers.logger, arguments.logLevel)  # DoltPy's Log Level
    logger.setLevel(arguments.logLevel)  # This Script's Log Level

    # TODO: Fix So Responds When Activated
    # if arguments.rover:
    rover: Rover = Rover(arguments.reply)

    # if arguments.archive:  # TODO: Fix Wait Time To Be Independent Of Archiver
    archiver: Archiver = Archiver(arguments.commit)
    server: WebServer = WebServer(1, "Analysis Server", 1)  # https://www.tutorialspoint.com/python3/python_multithreading.htm

    # Start Webserver
    if arguments.server:
        server.start()

    wait_time: int = arguments.wait * 60
    while 1:
        if arguments.archive:
            archiver.download_tweets()

        if arguments.rover:
            rover.look_for_tweets()

        # TODO: Implement Wait Time Check For Rover
        current_wait_time: int = wait_time
        if isinstance(archiver.wait_time, int):
            current_wait_time: int = wait_time if wait_time > archiver.wait_time else archiver.wait_time

        wait_unit: str = "Minute" if wait_time == 60 else "Minutes"  # Because I Keep Forgetting What This Is Called, It's Called A Ternary Operator
        logger.log(main_config.INFO_QUIET,
                   "Waiting For {time} {unit} Before Checking For New Tweets".format(time=int(current_wait_time/60),
                                                                                     unit=wait_unit))

        time.sleep(current_wait_time)


if __name__ == '__main__':
    # This is to get DoltPy's Logger To Shut Up When Running `this_script.py -h`
    logging.Logger.setLevel(system_helpers.logger, logging.CRITICAL)

    args = parser.parse_args()
    try:
        main(args)
    except KeyboardInterrupt:
        logger.warning("Exiting By User Request...")
        exit(0)
