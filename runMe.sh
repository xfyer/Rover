#!/bin/bash

source venv/bin/activate

while true; do
  echo "Checking For New Tweets"
  python3 main.py --log=info

  echo "Waiting 1 Minutes"
  sleep $((1*60))
done