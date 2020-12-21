#!/usr/bin/python
from typing import Optional

from doltpy.core import Dolt
from pypika import Query, Table, Order
from pypika.functions import Lower, Count
from pypika.queries import QueryBuilder


def latest_tweets(repo: Dolt, table: str, max_responses: int = 10, account_id: Optional[int] = None,
                  hide_deleted_tweets: bool = False, only_deleted_tweets: bool = False,
                  last_tweet_id: Optional[int] = None) -> dict:

    tweets: Table = Table(table)
    query: QueryBuilder = Query.from_(tweets) \
        .select(tweets.id, tweets.twitter_user_id, tweets.date,
                tweets.text, tweets.device, tweets.favorites,
                tweets.retweets, tweets.quoteTweets, tweets.replies,
                tweets.isRetweet, tweets.isDeleted, tweets.repliedToTweetId,
                tweets.repliedToUserId, tweets.repliedToTweetDate,
                tweets.retweetedTweetId, tweets.retweetedUserId,
                tweets.retweetedTweetDate, tweets.hasWarning, tweets.warningLabel) \
        .orderby(tweets.id, order=Order.desc) \
        .limit(max_responses)

    if account_id is not None:
        # Show Results For Specific Account
        query: QueryBuilder = query.where(tweets.twitter_user_id, account_id)

    if last_tweet_id is not None:
        query: QueryBuilder = query.where(tweets.id > last_tweet_id)

    if hide_deleted_tweets:
        # Filter Out Deleted Tweets
        query: QueryBuilder = query.where(tweets.isDeleted == 0)
    elif only_deleted_tweets:
        # Only Show Deleted Tweets
        query: QueryBuilder = query.where(tweets.isDeleted == 1)

    # Retrieve Latest Tweets
    return repo.sql(query=query.get_sql(quote_char=None), result_format="json")["rows"]


def search_tweets(search_phrase: str, repo: Dolt, table: str, max_responses: int = 10, account_id: Optional[int] = None,
                  hide_deleted_tweets: bool = False, only_deleted_tweets: bool = False) -> dict:

    tweets: Table = Table(table)
    query: QueryBuilder = Query.from_(tweets) \
        .select(tweets.id, tweets.twitter_user_id, tweets.date,
                tweets.text, tweets.device, tweets.favorites,
                tweets.retweets, tweets.quoteTweets, tweets.replies,
                tweets.isRetweet, tweets.isDeleted, tweets.repliedToTweetId,
                tweets.repliedToUserId, tweets.repliedToTweetDate,
                tweets.retweetedTweetId, tweets.retweetedUserId,
                tweets.retweetedTweetDate, tweets.hasWarning, tweets.warningLabel) \
        .orderby(tweets.id, order=Order.desc) \
        .limit(max_responses) \
        .where(Lower(tweets.text).like(search_phrase.lower()))  # TODO: lower(text) COLLATE utf8mb4_unicode_ci like lower('{search_phrase}')

    if account_id is not None:
        # Show Results For Specific Account
        query: QueryBuilder = query.where(tweets.twitter_user_id, account_id)

    if hide_deleted_tweets:
        # Filter Out Deleted Tweets
        query: QueryBuilder = query.where(tweets.isDeleted == 0)
    elif only_deleted_tweets:
        # Only Show Deleted Tweets
        query: QueryBuilder = query.where(tweets.isDeleted == 1)

    # Perform Search Query
    # Use Commit https://github.com/dolthub/dolt/commit/6089d7e15d5fe4b02a4dc13630289baee7f937b0 Until JSON Escaping Bug Is Fixed
    return repo.sql(query=query.get_sql(quote_char=None), result_format="json")["rows"]


def count_tweets(search_phrase: str, repo: Dolt, table: str, account_id: Optional[int] = None,
                 hide_deleted_tweets: bool = False, only_deleted_tweets: bool = False) -> int:

    tweets: Table = Table(table)
    query: QueryBuilder = Query.from_(tweets) \
        .select(Count(tweets.id)) \
        .orderby(tweets.id, order=Order.desc) \
        .where(Lower(tweets.text).like(search_phrase.lower()))  # TODO: lower(text) COLLATE utf8mb4_unicode_ci like lower('{search_phrase}')

    if account_id is not None:
        # Show Results For Specific Account
        query: QueryBuilder = query.where(tweets.twitter_user_id, account_id)

    if hide_deleted_tweets:
        # Filter Out Deleted Tweets
        query: QueryBuilder = query.where(tweets.isDeleted == 0)
    elif only_deleted_tweets:
        # Only Show Deleted Tweets
        query: QueryBuilder = query.where(tweets.isDeleted == 1)

    # Perform Count Query
    count_result = repo.sql(query=query.get_sql(quote_char=None), result_format="json")["rows"]

    # Retrieve Count of Tweets From Search
    for header in count_result[0]:
        return count_result[0][header]

    return -1
