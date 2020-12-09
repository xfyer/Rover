#!/usr/bin/python
import csv
import json
import logging
import math
import time
from json.decoder import JSONDecodeError
from typing import Optional, Union
import pandas as pd

from doltpy.core import Dolt
from doltpy.core.system_helpers import get_logger
from doltpy.etl import get_df_table_writer

from archiver import config
from archiver.tweet_api_two import BearerAuth, TweetAPI2
from config import config


class Archiver:
    def __init__(self):
        self.logger: logging.Logger = get_logger(__name__)
        self.INFO_QUIET: int = config.INFO_QUIET
        self.VERBOSE: int = config.VERBOSE

        # Setup Repo
        self.initRepo(path=config.ARCHIVE_TWEETS_REPO_PATH,
                      create=False,
                      url=config.ARCHIVE_TWEETS_REPO_URL)

        # Setup For Twitter API
        with open(config.CREDENTIALS_FILE_PATH, "r") as file:
            credentials = json.load(file)

        # Token
        token: BearerAuth = BearerAuth(token=credentials['BEARER_TOKEN'])

        # Twitter API V2
        self.twitter_api: TweetAPI2 = TweetAPI2(auth=token)

        # To Get Python To Quit Complaining About Init Outside Of __init__
        self.repo: Optional[Dolt] = None

        # Wait Time Remaining
        self.wait_time: Optional[int] = None

    def download_tweets(self):
        self.logger.log(self.INFO_QUIET, "Checking For New Tweets")

        # Get Current President Info
        president_info = self.lookupCurrentPresident()

        # Sanitize For Empty Results
        if len(president_info) < 1:
            self.logger.error("President Info is Missing!!! Returning From Archiver!!!")
            return

        president_id = president_info[0]["Twitter User ID"]
        table = president_info[0]["Database Name"]

        # Create Table If Not Exists
        self.createTableIfNotExists(table=table)

        # Download Tweets From File and Archive
        self.downloadNewTweets(president_id=president_id, table=table)
        # self.downloadTweetsFromFile(repo=repo, table=table, api=tAPI, path='presidential-tweets/download-ids.csv')
        # self.addTweetToDatabase(repo=repo, table=table, data=retrieveData('tests/cut-off-tweet.json'))

        # TODO: Determine If Needing If Is Required Here
        # Commit Changes If Any
        madeCommit = self.commitData(table=table, message=config.ARCHIVE_TWEETS_COMMIT_MESSAGE)

        # Don't Bother Pushing If Not Commit
        if madeCommit:
            self.pushData(branch=config.ARCHIVE_TWEETS_REPO_BRANCH)

    def lookupCurrentPresident(self) -> dict:
        current_time_query = '''
            SELECT CURRENT_TIMESTAMP;
        '''

        # I probably shouldn't be hardcoding the value of the query
        current_time = self.repo.sql(current_time_query, result_format='csv')[0]['CURRENT_TIMESTAMP()']

        self.logger.debug("Current SQL Time: {}".format(current_time))

        current_president_query = '''
            select `Twitter User ID`, `Database Name` from presidents where `Start Term`<'{current_date}' and (`End Term`>'{current_date}' or `End Term` is null) limit 1;
        '''.format(current_date=current_time)

        return self.repo.sql(current_president_query, result_format='csv')

    def lookupLatestTweet(self, table: str) -> Optional[str]:
        latest_tweet_id_query = '''
            select id from {table} order by id desc limit 1;
        '''.format(table=table)

        tweet_id = self.repo.sql(latest_tweet_id_query, result_format='csv')  # 1330487624402935808
        # tweet_id = "1331393812728573952"

        if len(tweet_id) < 1 or 'id' not in tweet_id[0]:
            return None

        return tweet_id[0]['id']

    def downloadNewTweets(self, table: str, president_id: str):
        # Last Tweet ID
        since_id = self.lookupLatestTweet(table=table)

        # Sanitization
        if since_id is None:
            resp = self.twitter_api.lookup_tweets(user_id=president_id)
        else:
            resp = self.twitter_api.lookup_tweets(user_id=president_id, since_id=since_id)

        tweets = json.loads(resp.text)

        tweetCount = 0
        for tweet in tweets:
            tweetCount = tweetCount + 1
            self.logger.log(self.INFO_QUIET, "Tweet {}: {}".format(tweet['id'], tweet['text']))

            full_tweet = self.downloadTweet(tweet_id=tweet['id'])

            # If Not A Tweet and Instead, The Rate Limit, Just Return
            if not isinstance(full_tweet, dict):
                return

            self.addTweetToDatabase(table=table, data=full_tweet)

        self.logger.log(self.INFO_QUIET, "Tweet Count: {}".format(tweetCount))

    def downloadTweet(self, tweet_id: str) -> Optional[dict]:
        resp = self.twitter_api.get_tweet(tweet_id=tweet_id)
        headers = resp.headers
        rateLimitResetTime = headers['x-rate-limit-reset']

        # Unable To Parse JSON. Chances Are Rate Limit's Been Hit
        try:
            return json.loads(resp.text)
        except JSONDecodeError:
            now = time.time()
            timeLeft = (float(rateLimitResetTime) - now)

            rateLimitMessage = 'Rate Limit Reset Time At {} which is in {} seconds ({} minutes)'.format(
                rateLimitResetTime, timeLeft, timeLeft / 60)

            self.wait_time = math.floor(timeLeft)

            self.logger.error(msg='Received A Non-JSON Value. Probably Hit Rate Limit.'.format(self.wait_time))
            self.logger.error(msg=rateLimitMessage)

    def lookupLatestArchivedTweet(self, table: str) -> str:
        latest_tweet = '''
            SELECT id FROM {table} ORDER BY date DESC LIMIT 1
        '''.format(table=table)

        return self.repo.sql(latest_tweet, result_format='csv')

    def downloadTweetsFromFile(self, table: str, path: str):
        with open(path, "r") as file:
            csv_reader = csv.reader(file, delimiter=',')
            line_count = -1
            for row in csv_reader:
                if line_count == -1:
                    self.logger.log(self.VERBOSE, f'Column names are {", ".join(row)}')
                    line_count += 1
                else:
                    self.logger.log(self.VERBOSE, f'\t{row[0]}')
                    line_count += 1

                    tweet = self.downloadTweet(tweet_id=row[0])

                    # If Not A Tweet and Instead, The Rate Limit, Just Return
                    if not isinstance(tweet, dict):
                        return

                    self.addTweetToDatabase(table=table, data=tweet)

                    # print(json.dumps(tweet, indent=4))
                    # print(tweet['data']['text'])

            self.logger.log(self.VERBOSE, f'Processed {line_count} lines.')

    def addTweetToDatabase(self, table: str, data: dict):
        # TODO: Figure Out If Tweet Still Accessible Despite Some Error Messages
        if 'errors' in data and data['errors'][0]['parameter'] == 'id':
            errorMessage = self.archiveErrorMessage(data)

            create_table = '''
                UPDATE {table}
                set
                    isDeleted="{isDeleted}",
                    json="{json}"
                where
                    id={id}
            '''.format(table=table, id=errorMessage['id'], isDeleted=errorMessage['isDeleted'],
                       json=errorMessage['json'])

            self.repo.sql(create_table, result_format='csv')
            return

        # Tweet Data
        tweet = self.extractTweet(data)
        df = self.getDataFrame(tweet)

        # Use `python3 this-script.py --log=VERBOSE` in order to see this output
        self.logger.log(self.VERBOSE, json.dumps(tweet, indent=4))

        self.writeData(table=table, dataFrame=df, requiredKeys=['id'])

        # Debug DataFrame
        # debugDataFrame(df)

    def debugDataFrame(self, dataFrame: pd.DataFrame):
        # Setup Print Options
        pd.set_option('display.max_colwidth', None)
        pd.set_option('max_columns', None)

        # Print DataFrame Info
        self.logger.log(self.VERBOSE, "DataFrame: ")
        self.logger.log(self.VERBOSE, dataFrame.head())

    def retrieveData(self, path: str) -> dict:
        # Read JSON From File
        with open(path) as f:
            data = json.load(f)

        # Print JSON For Debugging
        self.logger.log(self.VERBOSE, data)

        return data

    def archiveErrorMessage(self, data: dict) -> dict:
        # for error in data['errors']:

        return {
            # Tweet ID
            'id': int(data['errors'][0]['value']),

            # Mark As Deleted
            'isDeleted': 1,  # Currently hardcoded

            # Raw Json For Future Processing
            'json': data
        }

    def extractTweet(self, data: dict) -> dict:
        # Extract Tweet Info
        tweet = data['data']
        metadata = data['includes']

        # RETWEET SECTION ----------------------------------------------------------------------

        # Detect if Retweet
        isRetweet = False
        retweetedTweetId = None
        iteration = -1

        # If Has Referenced Tweets Key
        if 'referenced_tweets' in tweet:
            for refTweets in tweet['referenced_tweets']:
                iteration = iteration + 1

                if refTweets['type'] == 'retweeted':
                    isRetweet = True
                    retweetedTweetId = refTweets['id']
                    break

        # Get Retweeted User's ID and Tweet Date
        retweetedUserId = None
        retweetedTweetDate = None

        # Pull From Same Iteration
        if 'tweets' in metadata and isRetweet and iteration < len(metadata['tweets']):
            retweetedUserId = metadata['tweets'][iteration]['author_id']
            retweetedTweetDate = metadata['tweets'][iteration]['created_at']

        self.logger.debug("Retweeted User ID: " + ("Not Set" if retweetedUserId is None else retweetedUserId))
        self.logger.debug("Retweeted Tweet ID: " + ("Not Set" if retweetedTweetId is None else retweetedTweetId))
        self.logger.debug("Retweeted Tweet Date: " + ("Not Set" if retweetedTweetDate is None else retweetedTweetDate))

        # REPLY SECTION ----------------------------------------------------------------------

        repliedToTweetId = None
        repliedToUserId = None
        repliedToTweetDate = None
        isReplyTweet = False
        iteration = -1

        # If Has Referenced Tweets Key
        if 'referenced_tweets' in tweet:
            for refTweets in tweet['referenced_tweets']:
                iteration = iteration + 1

                if refTweets['type'] == 'replied_to':
                    isReplyTweet = True
                    repliedToTweetId = refTweets['id']
                    break

        if 'tweets' in metadata and isReplyTweet and iteration < len(metadata['tweets']):
            repliedToUserId = metadata['tweets'][iteration]['author_id']
            repliedToTweetDate = metadata['tweets'][iteration]['created_at']

        self.logger.debug("Replied To User ID: " + ("Not Set" if repliedToUserId is None else repliedToUserId))
        self.logger.debug("Replied To Tweet ID: " + ("Not Set" if repliedToTweetId is None else repliedToTweetId))
        self.logger.debug("Replied To Tweet Date: " + ("Not Set" if repliedToTweetDate is None else repliedToTweetDate))

        # EXPANDED URLS SECTION ----------------------------------------------------------------------

        # Look For Expanded URLs in Tweet
        expandedUrls = None

        if 'entities' in tweet and 'urls' in tweet['entities']:
            expandedUrls = ""  # Set to Blank String

            # Loop Through Expanded URLs
            for url in tweet['entities']['urls']:
                expandedUrls = expandedUrls + url['expanded_url'] + ', '

            # Remove Extra Comma
            expandedUrls = expandedUrls[:-2]

        # FULL TWEET TEXT SECTION ----------------------------------------------------------------------

        # TODO: Implement Full Tweet Text Finding/Storage
        # if 'tweets' in metadata:
        #     text = ""  # Set to Blank String

        #     # Loop Through Referenced Tweets
        #     for tweet in tweet['tweets']:
        #         text = tweet['text']
        #         break

        # FORM DICTIONARY SECTION ----------------------------------------------------------------------

        return {
            'id': tweet['id'],

            # This Tweet's Metadata
            'date': tweet['created_at'],
            'text': tweet['text'],
            'device': tweet['source'],

            # Engagement Statistics
            'favorites': tweet['public_metrics']['like_count'],
            'retweets': tweet['public_metrics']['retweet_count'],
            'quoteTweets': tweet['public_metrics']['quote_count'],
            'replies': tweet['public_metrics']['reply_count'],

            # This Tweet's Booleans
            'isRetweet': int(isRetweet),
            'isDeleted': 0,  # Currently hardcoded

            # Replied Tweet Info
            'repliedToTweetId': repliedToTweetId,
            'repliedToUserId': repliedToUserId,
            'repliedToTweetDate': repliedToTweetDate,

            # Retweet Info
            'retweetedTweetId': retweetedTweetId,
            'retweetedUserId': retweetedUserId,
            'retweetedTweetDate': retweetedTweetDate,

            # Expanded Urls
            'expandedUrls': expandedUrls,

            # Raw Json For Future Processing
            'json': json.dumps(data)
        }

    def getDataFrame(self, tweet: dict) -> pd.DataFrame:
        # Import JSON Into Panda DataFrame
        return pd.DataFrame([tweet])

    def initRepo(self, path: str, create: bool, url: str = None):
        # Prepare Repo For Data
        if create:
            repo = Dolt.init(path)
            repo.remote(add=True, name='origin', url=url)
            self.repo: Dolt = repo

        self.repo: Dolt = Dolt(path)

    def writeData(self, table: str, dataFrame: pd.DataFrame, requiredKeys: list):
        # Prepare Data Writer
        raw_data_writer = get_df_table_writer(table, lambda: dataFrame, requiredKeys)

        # Write Data To Repo
        raw_data_writer(self.repo)

    def createTableIfNotExists(self, table: str) -> str:
        columns = '''
            `id` bigint unsigned NOT NULL,
            `date` datetime NOT NULL,
            `text` longtext NOT NULL,
            `device` longtext NOT NULL,
            `favorites` bigint unsigned NOT NULL,
            `retweets` bigint unsigned NOT NULL,
            `quoteTweets` bigint unsigned,
            `replies` bigint unsigned,
            `isRetweet` tinyint NOT NULL,
            `isDeleted` tinyint NOT NULL,
            `repliedToTweetId` bigint unsigned,
            `repliedToUserId` bigint unsigned,
            `repliedToTweetDate` datetime,
            `retweetedTweetId` bigint unsigned,
            `retweetedUserId` bigint unsigned,
            `retweetedTweetDate` datetime,
            `expandedUrls` longtext,
            `json` longtext,
            PRIMARY KEY (`id`)
        '''

        settings = '''
            ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        '''

        create_table = '''
            CREATE TABLE IF NOT EXISTS {table} ({columns}) {settings}
        '''.format(table=table, columns=columns, settings=settings)

        return self.repo.sql(create_table, result_format='csv')

    def commitData(self, table: str, message: str) -> bool:
        # Check to ensure changes need to be added first
        if not self.repo.status().is_clean:
            self.repo.add(table)
            self.repo.commit(message)
            return True
        return False

    def pushData(self, branch: str):
        self.repo.push('origin', branch)
