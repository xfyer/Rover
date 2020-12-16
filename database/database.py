#!/usr/bin/python
from typing import Optional

from doltpy.core import Dolt


def latest_tweets(repo: Dolt, table: str, max_responses: int = 10, account_id: Optional[int] = None,
                  hide_deleted_tweets: bool = False, only_deleted_tweets: bool = False, last_tweet_id: Optional[int] = None) -> dict:

    handle_account_id: str = "" if account_id is None else f"where twitter_user_id={account_id}"

    clause: str = "where" if (handle_account_id == "") else "and"

    handle_deleted: str = f"{clause} isDeleted=0" if hide_deleted_tweets else ""  # Determine If Should Filter Out Deleted Tweets
    handle_deleted: str = handle_deleted if not only_deleted_tweets else "{clause} isDeleted=1"  # Only Show Deleted Tweets

    clause: str = "where" if (handle_deleted == "") else "and"

    handle_last_tweet: str = "" if last_tweet_id is None else f"{clause} id>{last_tweet_id}"

    # Format Latest Tweets Query
    columns: str = "id, twitter_user_id, date, text, device, favorites, retweets, quoteTweets, replies, isRetweet, isDeleted, repliedToTweetId, repliedToUserId, repliedToTweetDate, retweetedTweetId, retweetedUserId, retweetedTweetDate, hasWarning, warningLabel"
    latest_tweets_query = f'''
        select {columns} from {table} {handle_account_id} {handle_deleted} {handle_last_tweet} order by id desc limit {max_responses};
    '''

    # Retrieve Latest Tweets
    return repo.sql(query=latest_tweets_query, result_format="json")["rows"]


def search_tweets(search_phrase: str, repo: Dolt, table: str, max_responses: int = 10, account_id: Optional[str] = None,
                  hide_deleted_tweets: bool = False, only_deleted_tweets: bool = False) -> dict:
    handle_deleted: str = "and isDeleted=0" if hide_deleted_tweets else ""  # Determine If Should Filter Out Deleted Tweets
    handle_deleted: str = handle_deleted if not only_deleted_tweets else "and isDeleted=1"  # Only Show Deleted Tweets

    handle_account_id: str = "" if account_id is None else f"and twitter_user_id={account_id}"

    # Format Search Query - TODO: Sanitize For Twitter User ID
    search_query = f'''
        select * from {table} where lower(text) COLLATE utf8mb4_unicode_ci like lower('{search_phrase}') {handle_deleted} {handle_account_id} order by id desc limit {max_responses};
    '''

    # Perform Search Query
    # Use Commit https://github.com/dolthub/dolt/commit/6089d7e15d5fe4b02a4dc13630289baee7f937b0 Until JSON Escaping Bug Is Fixed
    return repo.sql(query=search_query, result_format="json")["rows"]


def count_tweets(search_phrase: str, repo: Dolt, table: str, account_id: Optional[str] = None,
                 hide_deleted_tweets: bool = False, only_deleted_tweets: bool = False) -> int:
    handle_deleted: str = "and isDeleted=0" if hide_deleted_tweets else ""  # Determine If Should Filter Out Deleted Tweets
    handle_deleted: str = handle_deleted if not only_deleted_tweets else "and isDeleted=1"  # Only Show Deleted Tweets

    handle_account_id: str = "" if account_id is None else f"and twitter_user_id={account_id}"

    # Format Count Search Query - TODO: Sanitize For Twitter User ID
    count_search_query = f'''
        select count(id) from {table} where lower(text) COLLATE utf8mb4_unicode_ci like lower('{search_phrase}') {handle_deleted} {handle_account_id};
    '''

    # Perform Count Query
    count_result = repo.sql(query=count_search_query, result_format="json")["rows"]

    # Retrieve Count of Tweets From Search
    for header in count_result[0]:
        return count_result[0][header]

    return -1
