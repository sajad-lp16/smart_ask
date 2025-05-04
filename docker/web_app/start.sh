#!/bin/bash

export PYTHONPATH=$PWD

cd ${PWD}

uvicorn web_app.fastapi_app:app --host 0.0.0.0 --port 8089 --workers 4 --loop asyncio &
python mattermost/main.py &

wait