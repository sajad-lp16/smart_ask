import re
import os
import json

from core import STEP_2_TICKETS_TARGET, STEP_1_TICKETS_TARGET
from parsing.parse_html import markup_remover
from parsing.parse_emails import get_unique_emails


def extract_conversations(current_speaker, html_source):
    text = markup_remover(html_source).strip()

    messages = re.split(r'(From: .*?:|De: .*?:|Von: .*?:|Van: .*?:|[^,]+ wrote:)', text)

    messages = [msg.strip() for msg in messages if msg.strip()]

    conversation = []

    for msg in messages:
        if msg.startswith("From:") or msg.startswith("De:") or msg.startswith("Von:") or msg.startswith("Van:"):
            try:
                current_speaker = ''.join(re.search(r":\s?(.*?)(>|\s)[\S]+:", msg).groups()).strip()
            except Exception as err:
                pass
            continue
        elif msg.endswith("wrote:"):
            current_speaker = re.split(r"(PM|AM)", msg.split("wrote:")[0])[-1].strip()

            continue
        conversation.append(f"{current_speaker}:\n{msg.strip()}")

    return "\n----\n\n".join(conversation)


def message_2_md_parser(messages: dict | list[dict], bulk=False) -> str:
    def _process_message(_message):
        if message["body"].startswith("From Bot:"):
            return ""
        current_speaker = message.get("origin_by") or message.get("from") or message.get("created_by")
        return extract_conversations(current_speaker, message["body"])

    if bulk:
        articles = []

        for message in messages:
            articles.append(_process_message(message))

        return "------\n\n".join(list(filter(lambda item: item, articles)))

    return _process_message(messages)


def parse_all_tickets_md():
    step_1_target = str(STEP_1_TICKETS_TARGET) + "_OK"
    step_2_target = STEP_2_TICKETS_TARGET

    os.makedirs(str(step_2_target), exist_ok=True)

    all_files = set(os.listdir(step_1_target))
    pre_processed = set(os.listdir(step_2_target))

    files_to_process = list(all_files - pre_processed)

    for file_name in files_to_process:
        with open(f"{step_1_target}/{file_name}") as file:
            ticket_articles = json.load(file)

        new_data = {
            "conversations": message_2_md_parser(ticket_articles, bulk=True),
            "all_emails": get_unique_emails(json.dumps(ticket_articles)),
            "ticket_id": file_name.split(".")[0]
        }

        with open(step_2_target / file_name, "w") as file:
            json.dump(new_data, file, ensure_ascii=False, indent=4)
