import os
import json


def json_topic_2_conversation(topic_json: dict) -> str:
    conversation = ""

    data = topic_json["post_stream"]["posts"]
    for post in data:
        name = post["name"]
        talk = post["cooked"]
        conversation += f"{name}: {talk}\n\n"

    return conversation
