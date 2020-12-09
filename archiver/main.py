#!/usr/bin/python

import argparse
from json import JSONDecodeError
from typing import Union, Optional

import pandas as pd
import json
import logging
import csv
import time
import math

from doltpy.core import Dolt, system_helpers
from doltpy.etl import get_df_table_writer
from doltpy.core.system_helpers import get_logger

from tweetdownloader import TweetDownloader, BearerAuth

from archiver import config


def main(arguments: argparse.Namespace):

    while 1:


        # Wait Regardless Of If Hit Limit Or Not
        wait_time = (arguments.wait * 60) if not isinstance(wait_time, int) else wait_time
        wait_unit: str = "Minute" if wait_time == 60 else "Minutes"  # Because I Keep Forgetting What This Is Called, It's Called A Ternary Operator
        logger.log(INFO_QUIET, "Waiting For {time} {unit} Before Checking For New Tweets".format(time=int(wait_time/60), unit=wait_unit))
        time.sleep(wait_time)


