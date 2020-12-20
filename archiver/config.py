#!/usr/bin/python

import os

# Working Directory
WORKING_DIRECTORY: str = "working"

# Dolt Repo Vars
ARCHIVE_TWEETS_REPO_URL: str = "alexis-evelyn/presidential-tweets"
ARCHIVE_TWEETS_REPO_PATH: str = os.path.join(WORKING_DIRECTORY, "presidential-tweets")
ARCHIVE_TWEETS_TABLE: str = "tweets"
ARCHIVE_TWEETS_COMMIT_MESSAGE: str = "Automated Tweet Update"
ARCHIVE_TWEETS_REPO_BRANCH: str = "master"

# Config Files
CREDENTIALS_FILE_PATH: str = "credentials.json"

# Failed Tweets File
FAILED_TWEETS_FILE_PATH: str = os.path.join(ARCHIVE_TWEETS_REPO_PATH, "failed_to_add_tweets.json")