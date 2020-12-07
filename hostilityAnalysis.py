#!/usr/bin/python
# https://www.analyticsvidhya.com/blog/2018/02/the-different-methods-deal-text-data-predictive-python/

import twitter


class HostilityAnalysis:
    def __init__(self, tweet: twitter.api.Status):
        self.tweet: twitter.api.Status = tweet
