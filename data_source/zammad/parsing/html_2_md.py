import re
import os
import json

from core import STEP_2_TICKETS_TARGET, STEP_1_TICKETS_TARGET
from data_source.zammad.parsing.parse_html import markup_remover
from data_source.zammad.parsing.parse_emails import get_unique_emails


def shorten_text(original_text, chunk_size=100):
    chunks = [original_text[i:i + chunk_size] for i in range(0, len(original_text), chunk_size)]

    seen = set()
    unique_chunks = []

    for chunk in chunks:
        if chunk not in seen:
            seen.add(chunk)
            unique_chunks.append(chunk)

    shortened_text = ''.join(unique_chunks)

    return shortened_text

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


def message_2_md_parser(messages: list[dict]) -> str:
    def _process_message(_message):
        if message["body"].startswith("From Bot:"):
            return ""
        current_speaker = _message.get("origin_by") or _message.get("from") or _message.get("created_by")
        return extract_conversations(current_speaker, message["body"])

    articles = []

    for message in messages:
        articles.append(_process_message(message))

    return shorten_text("------\n\n".join(list(filter(lambda item: item, articles))))


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
            "conversations": message_2_md_parser(ticket_articles),
            "all_emails": get_unique_emails(json.dumps(ticket_articles)),
            "ticket_id": file_name.split(".")[0]
        }

        with open(step_2_target / file_name, "w") as file:
            json.dump(new_data, file, ensure_ascii=False, indent=4)
