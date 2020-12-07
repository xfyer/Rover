#!/usr/bin/python
# Tutorial: https://www.analyticsvidhya.com/blog/2018/02/the-different-methods-deal-text-data-predictive-python/
import json

import nltk
import twitter
from nltk.corpus import stopwords
from typing import List
from textblob import TextBlob
import pandas as pd


def avg_word(sentence) -> float:
    words = sentence.split()
    return sum(len(word) for word in words) / len(words)


class HostilityAnalysis:
    def __init__(self):
        # nltk.download('stopwords')
        self.stop_words: List[str] = stopwords.words('english')
        self.tweets: pd.DataFrame = pd.DataFrame()

    def add_tweet_to_process(self, tweet: json):
        # print("ORIGINAL VALUE: '{text}'".format(text=tweet["text"]))

        # self.tweet: json = tweet
        analysis_data: json = {
            "text": tweet["text"],
            "word_count": len(tweet["text"].split(" ")),
            "character_count": len(tweet["text"]),
            "average_word_count": avg_word(tweet["text"]),
            "stop_words_count": len([tweet["text"] for tweet["text"] in tweet["text"].split() if tweet["text"] in self.stop_words]),
            "hashtag_count": len([tweet["text"] for tweet["text"] in tweet["text"].split() if tweet["text"].startswith('#')]),
            "numeric_count": len([tweet["text"] for tweet["text"] in tweet["text"].split() if tweet["text"].isdigit()]),
            "uppercase_word_count": len([tweet["text"] for tweet["text"] in tweet["text"].split() if tweet["text"].isupper()]),
            "lowercase_word_count": len([tweet["text"] for tweet["text"] in tweet["text"].split() if tweet["text"].islower()])
        }

        # TODO: Fix tweet["text"]
        self.tweets = self.tweets.append(analysis_data, ignore_index=True)
        print(self.tweets)
        print(tweet["text"])
        exit(0)

    def preprocess_tweet(self):
        # False Warning: https://youtrack.jetbrains.com/issue/PY-43841
        self.tweets["text"]: pd.DataFrame = self.tweets["text"].apply(lambda x: " ".join(x.lower() for x in x.split()))  # Convert To Lowercase To Avoid Duplicate Words
        self.tweets["text"]: pd.DataFrame = self.tweets["text"].replace('[^\\w\\s]', '')  # Remove Punctuation
        self.tweets["text"]: pd.DataFrame = self.tweets["text"].apply(lambda x: " ".join(x for x in x.split() if x not in self.stop_words))  # Remove Stop Words

        most_common_words = pd.Series(' '.join(self.tweets['text']).split()).value_counts()[:10]  # Prepare To Remove 10 Most Common Words
        freq: List[int] = list(most_common_words.index)  # Create List of 10 Most Common Words
        self.tweets["text"]: pd.DataFrame = self.tweets['text'].apply(lambda x: " ".join(x for x in x.split() if x not in freq))  # Apply List of 10 Most Common Words
        self.tweets["text"].head()

        least_common_words = pd.Series(' '.join(self.tweets['text']).split()).value_counts()[-10:]  # Prepare To Remove 10 Most Common Words  # Prepare To Remove 10 Least Common Words
        freq: List[int] = list(least_common_words.index)  # Create List of 10 Least Common Words
        self.tweets["text"]: pd.DataFrame = pd.Series(' '.join(self.tweets['text']).split()).value_counts()[-10:]  # Apply List of 10 Most Common Words
        self.tweets["text"].head()

        # self.tweets["text"]: pd.DataFrame = self.tweets['text'][:5].apply(lambda x: str(TextBlob(x).correct()))  # Correct Spelling For Mistyped Words
        print(self.tweets['text'])

        # TODO: 2.7 Tokenization From https://www.analyticsvidhya.com/blog/2018/02/the-different-methods-deal-text-data-predictive-python/
