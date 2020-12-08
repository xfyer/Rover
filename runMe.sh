#!/bin/bash

if [ -f "./venv/bin/activate" ]
then
    echo "Using Venv ./venv/"
    source ./venv/bin/activate
fi

python3 main.py --log=info