from bs4 import BeautifulSoup
import re


class EmailSeparator:
    def __init__(self):
        # Common patterns for different email clients and languages
        # Each pattern must be very specific to avoid false positives
        outlook_style = (
            r"(?:^|\n)"
            r"[\s>]*(?:\*\*)?(?:From|Von|De|Van) *: *(?:\*\*)?.+?\n"
            r"[\s>]*(?:\*\*)?(?:Sent|Gesendet|Envoyé|Verzonden) *: *(?:\*\*)?.+?\n"
            r"[\s>]*(?:\*\*)?(?:To|An|À|Aan) *: *(?:\*\*)?.+?\n"
            r"[\s>]*(?:\*\*)?(?:Subject|Betreff|Objet|Onderwerp) *: *(?:\*\*)?.+?\n"  # codespell:ignore
        )
        forwarded_message = (
            r"(?:^|\n)"
            r"[\s>]*-{3,} Forwarded message -{3,}\n"
            r"From *:.*?\n"
            r"Date *:.*?\n"
            r"Subject:.*?\n"
            r"To:.*?\n"
        )
        ethica_forwarded_msg = (
            r"On (?:[A-Za-z]{3}), (?:[A-Za-z]{3}) \d{1,2}, "
            r"\d{4} at \d{1,2}:\d{2} (?:AM|PM) ([A-Za-z\s]+) "
            r"via ([A-Za-z\s]+)[\s\n]+"
            r"<([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})> wrote:"
        )
        # Gmail/Generic style - Must have date and "wrote" in specific format
        on_wrote_format = (
            r"(?:^|\n)"
            r"[\s>]*On [A-Za-z]{3,9},?\s+[A-Za-z]{3,9}\s+\d{1,2},"
            r"?\s+\d{4}(?:\s+at\s+\d{1,2}:\d{2}(?::\d{2})?\s*"
            r"(?:AM|PM|am|pm)?)?[\s,]+(?:[^<\n]+ )?(?:<[^>]+>)?\s*wrote:\s*\n"
        )
        self.patterns = [
            outlook_style,
            forwarded_message,
            on_wrote_format,
            ethica_forwarded_msg,
            # Common quote markers - Must be at start of line and followed by content
            r"(?:^|\n)[\s>]*>+(?:\s*>)*(?=\s*[A-Za-z0-9])",  # Quote markers followed by content
            # Common divider patterns - Must be long enough and on their own line
            r"(?:^|\n)[\s>]*(?:_+-){10,}(?:\s*\n|$)",  # Alternating underscores and hyphens
            r"(?:^|\n)[\s>]*_{20,}(?:\s*\n|$)",  # Long sequence of underscores
            r"(?:^|\n)[\s>]*-{20,}(?:\s*\n|$)",  # Long sequence of hyphens
        ]

        # Compile all patterns
        self.compiled_patterns = [re.compile(pattern, re.MULTILINE | re.DOTALL) for pattern in self.patterns]

    def validate_quote_marker(self, text: str, match_start: int) -> bool:
        """
        Additional validation to reduce false positives.
        Returns True if this really looks like a quote marker.
        """
        # Get the context around the match (up to 500 chars before and after)
        context_start = max(0, match_start - 500)
        context_end = min(len(text), match_start + 500)
        context = text[context_start:context_end]

        # Look for indicators that this is really a quote
        indicators = [
            # Check if there's an email address nearby
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            # Check for date patterns
            r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}",
            r"\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?",
            # Check for common reply indicators
            r"(?:wrote|schrieb|écrit|escribió|scrisse|schreef):",
        ]

        # Must match at least one indicator within the context
        for indicator in indicators:
            if re.search(indicator, context):
                return True

        return False

    def find_first_quote_marker(self, text: str) -> tuple[int, str] | None:
        """
        Find the first occurrence of any quote marker pattern in the text.
        Returns tuple of (start_position, matched_text) or None if no match found.
        """
        earliest_match = None
        earliest_pos = len(text)

        for pattern in self.compiled_patterns:
            match = pattern.search(text)
            if match:
                # Additional validation to reduce false positives
                if self.validate_quote_marker(text, match.start()):
                    if match.start() < earliest_pos:
                        earliest_pos = match.start()
                        earliest_match = match.group()

        return (earliest_pos, earliest_match) if earliest_match else None

    def separate_email(self, email_text: str) -> str:
        email_text = "\n" + email_text.replace("\r\n", "\n")

        # Initialize result lists
        main_content = email_text
        return self.clean_content(main_content)

    def clean_content(self, content: str) -> str:
        """
        Clean up the extracted content by removing extra whitespace,
        empty lines at start/end, etc.
        """
        content = content.replace("\\n", "")
        content = re.sub(r"[\s]{2,}", " ", content)
        lines = content.split("\n")
        # Remove empty lines from start and end
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        return " ".join(lines)


def markup_remover(html_source):
    email_separator = EmailSeparator()
    soup = BeautifulSoup(html_source, 'html.parser')
    text = soup.get_text()

    main_content = email_separator.separate_email(text)

    return main_content
