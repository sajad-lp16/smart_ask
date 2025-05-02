#!/bin/bash

export PYTHONPATH=$PWD

python web_app/fastapi_app.py &
python mattermost/main.py &
wait