#!/usr/bin/python

import os

# Working Directory
WORKING_DIRECTORY: str = "working"

# Dolt Repo Vars
ARCHIVE_TWEETS_REPO_URL: str = "alexis-evelyn/test"
ARCHIVE_TWEETS_REPO_PATH: str = os.path.join(WORKING_DIRECTORY, "presidential-tweets")
ARCHIVE_TWEETS_TABLE: str = "trump"
ARCHIVE_TWEETS_COMMIT_MESSAGE: str = "Automated Tweet Update"
ARCHIVE_TWEETS_REPO_BRANCH: str = "master"

# Config Files
CREDENTIALS_FILE_PATH: str = "credentials.json"
