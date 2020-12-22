#!/usr/bin/python

import json
from typing import Optional

from doltpy.core import Dolt

from rover import config, search_tweets
from database import database

from urllib.parse import urlparse, parse_qs


def handle_api(self):
    # Repo
    repo: Dolt = Dolt(config.ARCHIVE_TWEETS_REPO_PATH)
    table: str = config.ARCHIVE_TWEETS_TABLE

    # Determine Reply and Send It
    send_reply(self=self, repo=repo, table=table)


def send_headers(self, content_length: int = 0):
    self.send_response(200)
    self.send_header("Content-type", "application/json")

    if config.ALLOW_CORS:
        self.send_header("Access-Control-Allow-Origin", config.CORS_SITES)

    self.send_header("Content-Length", content_length)

    self.end_headers()


def send_reply(self, repo: Dolt, table: str):
    url: urlparse = urlparse(self.path)
    queries: dict = parse_qs(url.query)

    response_dict: dict = run_function(repo=repo, table=table, url=url, queries=queries)

    response: str = json.dumps(response_dict)
    content_length: int = len(response)

    # logger.debug(f"Content Length: {content_length}")

    # Determine Headers To Send and Send Them
    send_headers(self=self, content_length=content_length)

    self.wfile.write(bytes(response, "utf-8"))


def run_function(repo: Dolt, table: str, url: urlparse, queries: dict) -> dict:
    endpoints = {
        '/api': send_help,
        '/api/latest': load_latest_tweets,
        '/api/search': perform_search,
        '/api/accounts': lookup_account
    }

    func = endpoints.get(url.path.rstrip('/'), invalid_endpoint)
    return func(repo=repo, table=table, queries=queries)


def load_latest_tweets(repo: Dolt, table: str, queries: dict) -> dict:
    """
        Load Latest Tweets. Can Be From Account And/Or Paged.
        :param repo: Dolt Repo Path
        :param table: Table To Query
        :param queries: GET Queries Dictionary
        :return: JSON Response
    """
    max_responses: int = int(queries['max'][0]) if "max" in queries and validateRangedNumber(value=queries['max'][0],
                                                                                             min=0, max=20) else 20

    last_tweet_id: Optional[int] = int(queries['tweet'][0]) if "tweet" in queries and validateNumber(value=queries['tweet'][0]) else None

    latest_tweets: dict = convertIDsToString(
        results=database.latest_tweets(repo=repo, table=table, max_responses=max_responses, last_tweet_id=last_tweet_id))

    response: dict = {
        "results": latest_tweets
    }

    if len(latest_tweets) > 0:
        response['latest_tweet_id'] = latest_tweets[0]['id']

    return response


def lookup_account(repo: Dolt, table: str, queries: dict) -> dict:
    if "account" not in queries:
        # TODO: Create A Proper Error Handler To Ensure Error Messages and IDs Are Standardized
        return {
            "error": "No Account ID Specified",
            "code": 2
        }

    # TODO: Implement Proper Way To Kill Abusers
    # To Prevent Hanging The Server
    max_results: int = 10

    # Results To Return
    results: dict = {"accounts": []}

    found_a_result: bool = False
    count: int = 0
    for account_id_str in queries["account"]:
        # Don't Let Above Max Results To Prevent Hanging
        if count >= max_results:
            break

        # Make Sure Always Counted
        count = count + 1

        account_id: int = int(account_id_str) if "account" in queries and validateNumber(value=account_id_str) else None

        # No Valid Id, So Skip
        if account_id is None:
            continue

        accounts: dict = database.retrieveAccountInfo(repo=repo, account_id=account_id)

        # No Results, So Skip
        if len(accounts) < 1:
            continue

        found_a_result: bool = True

        results["accounts"].append({
            "account_id": str(account_id),
            "first_name": accounts[0]["first_name"],
            "last_name": accounts[0]["last_name"],
            "handle": accounts[0]["twitter_handle"],
            "notes": accounts[0]["notes"]
        })

    if not found_a_result:
        return {
            "error": "No Results Found!!!",
            "code": 3
        }

    return results


def perform_search(repo: Dolt, table: str, queries: dict) -> dict:
    original_search_text: str = queries["text"][0] if "text" in queries else ""

    search_phrase: str = search_tweets.convert_search_to_query(phrase=original_search_text)

    search_results: dict = convertIDsToString(
        results=database.search_tweets(search_phrase=search_phrase, repo=repo, table=table))
    tweet_count: int = database.count_tweets(search_phrase=search_phrase, repo=repo, table=table)

    return {
        "search_text": original_search_text,
        "count": tweet_count,
        "results": search_results
    }


def send_help(repo: Dolt, table: str, queries: dict) -> dict:
    """
        Used To Indicate Existing API Endpoints
        :return: JSON Response With URLs
    """
    return {
        "endpoints": [
            {"/api": "Query List of Endpoints"},
            {"/api/latest": "Retrieve Newest Tweets"},
            {"/api/search": "Search For Tweets"},
            {"/api/accounts": "Lookup Account Info By ID"}
        ],
        "note": "Future Description of Query Parameters Are On My Todo List"
    }


def invalid_endpoint(repo: Dolt, table: str, queries: dict) -> dict:
    """
        Used To Indicate Reaching an API Url That Doesn't Exist
        :return: JSON Error Message With Code For Machines To Process
    """
    return {
        "error": "Invalid Endpoint",
        "code": 1
    }


def convertIDsToString(results: dict):
    for result in results:
        result["twitter_user_id"] = str(result["twitter_user_id"])
        result["id"] = str(result["id"])

        # Account ID of Tweet That Was Retweeted
        if "retweetedUserId" in result:
            result["retweetedUserId"] = str(result["retweetedUserId"])

        # Tweet ID of Tweet That Was Retweeted
        if "retweetedTweetId" in result:
            result["retweetedTweetId"] = str(result["retweetedTweetId"])

    return results


def validateNumber(value: str) -> bool:
    if not value.isnumeric():
        return False

    return True


def validateRangedNumber(value: str, min: int = 0, max: int = 100) -> bool:
    if not value.isnumeric():
        return False

    number: int = int(value)

    if number > max or number < min:
        return False

    return True
