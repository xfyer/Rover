#!/usr/bin/python

import json
import logging
import os
import random
from typing import Optional

import twitter
from PIL import Image, ImageDraw, ImageFont
from doltpy.core import Dolt

from rover import config
from rover.hostility_analysis import HostilityAnalysis
from rover.search_tweets import SafeDict, get_search_keywords, convert_search_to_query, get_username_by_id

logger: Optional[logging.Logger] = None
INFO_QUIET: Optional[int] = None
VERBOSE: Optional[int] = None


def process_command(api: twitter.Api, status: twitter.models.Status, logger_param: logging.Logger,
                    info_level: int = logging.INFO + 1,
                    verbose_level: int = logging.DEBUG - 1):

    global logger
    logger = logger_param

    global INFO_QUIET
    INFO_QUIET = info_level

    global VERBOSE
    VERBOSE = verbose_level

    # TODO: Implement Better Command Parsing Handling
    if "image" in status.full_text:
        draw_image(api=api, status=status)
    elif "hello" in status.full_text:
        say_hello(api=api, status=status)
    elif "search" in status.full_text:
        search_text(api=api, status=status)
    elif "analyze" in status.full_text:
        analyze_tweet(api=api, status=status)
    elif "help" in status.full_text:
        give_help(api=api, status=status)


def draw_image(api: twitter.Api, status: twitter.models.Status):
    if not os.path.exists(config.WORKING_DIRECTORY):
        os.makedirs(config.WORKING_DIRECTORY)

    with Image.new("RGB", (1024, 1024)) as im:
        draw = ImageDraw.Draw(im)

        # random.seed(time.time())
        r = random.random() * 255
        g = random.random() * 255
        b = random.random() * 255

        for x in range(0, im.size[0]):
            for y in range(0, im.size[0]):
                im.putpixel((x, y), (int(random.random() * r), int(random.random() * g), int(random.random() * b)))

        # draw.line((0, 0) + im.size, fill=128)
        # draw.line((0, im.size[1], im.size[0], 0), fill=128)

        # αℓєχιѕ єνєℓуη 🏳️‍⚧️ 🏳️‍🌈
        # Zero Width Joiner (ZWJ) does not seem to be supported, need to find a font that works with it to confirm it
        fnt = ImageFont.truetype(config.FONT_PATH, config.FONT_SIZE)
        length = int(config.IMAGE_NAME_OFFSET_MULTIPLIER * len(config.IMAGE_NAME))
        draw.multiline_text((im.size[0] - length, im.size[1] - 50), config.IMAGE_NAME, font=fnt,
                            fill=(int(255 - r), int(255 - g), int(255 - b)))

        # write to file like object
        # output = io.BytesIO()  # Why does the PostUpdate not work with general bytesio?
        im.save(config.TEMPORARY_IMAGE_PATH, config.TEMPORARY_IMAGE_FORMAT)

        new_status = "@{user}".format(user=status.user.screen_name)

        if config.REPLY:
            api.PostUpdate(in_reply_to_status_id=status.id, status=new_status, media=config.TEMPORARY_IMAGE_PATH)

        os.remove(config.TEMPORARY_IMAGE_PATH)  # Remove temporary file


def search_text(api: twitter.Api, status: twitter.models.Status):
    # Broken For Some Reason
    # select id, text from trump where text COLLATE utf8mb4_unicode_ci like '%sleepy%joe%' order by id desc limit 10;
    # select count(id) from trump where text COLLATE utf8mb4_unicode_ci like '%sleepy%joe%';

    # select id, text from trump where lower(text) COLLATE utf8mb4_unicode_ci like lower('%sleepy%joe%') order by id desc limit 10;
    # select count(id) from trump where lower(text) COLLATE utf8mb4_unicode_ci like lower('%sleepy%joe%');

    # print(status.tweet_mode)

    if status.tweet_mode == "extended":
        status_text = status.full_text
    else:
        status_text = status.text

    # This Variable Is Useful For Debugging Search Queries And Exploits
    original_phrase = get_search_keywords(text=status_text)

    repo: Dolt = Dolt(config.ARCHIVE_TWEETS_REPO_PATH)
    phrase = convert_search_to_query(phrase=original_phrase)

    search_query = '''
        select * from {table} where lower(text) COLLATE utf8mb4_unicode_ci like lower('{phrase}') order by id desc limit 10;
    '''.format(phrase=phrase, table=config.ARCHIVE_TWEETS_TABLE)

    count_search_query = '''
        select count(id) from {table} where lower(text) COLLATE utf8mb4_unicode_ci like lower('{phrase}');
    '''.format(phrase=phrase, table=config.ARCHIVE_TWEETS_TABLE)

    logger.debug(search_query)

    # Perform Search Queries
    count_result = repo.sql(query=count_search_query, result_format="json")["rows"]
    search_results = repo.sql(query=search_query, result_format="json")[
        "rows"]  # Use Commit https://github.com/dolthub/dolt/commit/6089d7e15d5fe4b02a4dc13630289baee7f937b0 Until JSON Escaping Bug Is Fixed
    # Load and Convert JSON in JSON Column - json.loads(results[0]["json"])

    # Retrieve Count of Tweets From Search
    count = -1
    for header in count_result[0]:
        count = count_result[0][header]
        logger.debug("Count For Phrase \"{search_phrase}\": {count}".format(search_phrase=original_phrase, count=count))
        break

    # Print Out 10 Found Search Results To Debug Logger
    loop_count = 0
    for result in search_results:
        logger.debug("Example Tweet For Phrase \"{search_phrase}\": {tweet_id} - {tweet_text}".format(
            search_phrase=original_phrase, tweet_id=result["id"], tweet_text=result["text"]))

        loop_count += 1
        if loop_count >= 10:
            break

    # Check To Make Sure Results Found
    if len(search_results) < 1:
        no_tweets_found_status = "@{user} No results found for \"{search_phrase}\"".format(user=status.user.screen_name,
                                                                                           search_phrase=original_phrase)

        if config.REPLY:
            api.PostUpdate(in_reply_to_status_id=status.id, status=no_tweets_found_status)

        logger.log(INFO_QUIET, "Sending Status: {new_status}".format(new_status=no_tweets_found_status))
        return

    search_post_response = search_results[0]
    author = get_username_by_id(api=api, author_id=json.loads(search_post_response["json"])["data"]["author_id"])
    url = "https://twitter.com/{screen_name}/statuses/{status_id}".format(status_id=search_post_response["id"],
                                                                          screen_name=author)

    if count == 1:
        word_times = "time"
    else:
        word_times = "times"

    new_status = "@{user} @{screen_name} has tweeted about \"{search_phrase}\" {search_count} {word_times}. The latest example is at {status_link}".format_map(
        SafeDict(
            user=status.user.screen_name, status_link=url, screen_name=author,
            search_count=count, word_times=word_times))

    truncate_amount = abs(
        (len('\u2026') + len("{search_phrase}") + twitter.api.CHARACTER_LIMIT - len(new_status)) - len(original_phrase))

    # Don't Put Ellipses If Search Is Not Truncated
    if (len(original_phrase) + len(new_status) + len('\u2026') - len("{search_phrase}")) >= twitter.api.CHARACTER_LIMIT:
        new_status = new_status.format(search_phrase=(original_phrase[:truncate_amount] + '\u2026'))
    else:
        new_status = new_status.format(search_phrase=original_phrase)

    logger.debug("Status Length: {length}".format(length=len(new_status)))

    # CHARACTER_LIMIT
    if config.REPLY:
        api.PostUpdates(in_reply_to_status_id=status.id, status=new_status, continuation='\u2026')

    logger.log(INFO_QUIET, "Sending Status: {new_status}".format(new_status=new_status))


def analyze_tweet(api: twitter.Api, status: twitter.models.Status):
    status_text = "12:00 A.M. on the Great Election Fraud of 2020!"  # status.full_text

    # This Variable Is Useful For Debugging Search Queries And Exploits
    original_phrase = get_search_keywords(text=status_text, search_word_query='analyze')

    repo: Dolt = Dolt(config.ARCHIVE_TWEETS_REPO_PATH)
    phrase = convert_search_to_query(phrase=original_phrase)

    search_query = '''
        select * from {table} where lower(text) COLLATE utf8mb4_unicode_ci like lower('{phrase}') order by id desc limit 10;
    '''.format(phrase=phrase, table=config.ARCHIVE_TWEETS_TABLE)

    search_results = repo.sql(query=search_query, result_format="json")["rows"]

    # Instantiate Text Processor
    analyzer: HostilityAnalysis = HostilityAnalysis(logger_param=logger, verbose_level=VERBOSE)

    # Load Tweets To Analyze
    for result in search_results:
        logger.log(VERBOSE, "Adding Tweet For Processing: {tweet_id} - {tweet_text}".format(tweet_id=result["id"], tweet_text=result["text"]))
        analyzer.add_tweet_to_process(result)

    analyzer.preprocess_tweets()
    analyzer.process_tweets()


def say_hello(api: twitter.Api, status: twitter.models.Status):
    new_status = "@{user} Hello {name}".format(name=status.user.name, user=status.user.screen_name)

    if config.REPLY:
        api.PostUpdate(in_reply_to_status_id=status.id, status=new_status)


def give_help(api: twitter.Api, status: twitter.models.Status):
    new_status = "@{user} Commands are image, hello, search, analyze (N/A), and help!!! E.g. for search, type {own_name} search your search text here\n\nI'm also working on a website for the bot. It's nowhere near ready right now though. https://alexisevelyn.me/".format(name=status.user.name, own_name=config.TWITTER_USER_HANDLE, user=status.user.screen_name)

    if config.REPLY:
        api.PostUpdate(in_reply_to_status_id=status.id, status=new_status, exclude_reply_user_ids=[config.TWITTER_USER_ID])
