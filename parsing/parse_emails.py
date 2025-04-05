import re

email_pattern = r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,30}@[a-zA-Z0-9]+\.[a-zA-Z]{2,}"


def get_unique_emails(text):
    return list(set(re.findall(email_pattern, text)))

