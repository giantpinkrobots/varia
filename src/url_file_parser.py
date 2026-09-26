import re
from urllib.parse import urlparse

# Matches http://, https://, ftp://, ftps://, and magnet: URIs (case-insensitive)
URL_REGEX = re.compile(r"(https?://|ftps?://|magnet:)", re.IGNORECASE)

# Characters that may legitimately appear at the end of a URL but are removed
# when they are actually trailing punctuation from surrounding text.
TRAILING_PUNCTUATION = ('.', ',', ';', ':', '!', '?', ')', ']', '}', '"', "'", '>')


def _clean_url(token):
    """Strip trailing punctuation from a candidate URL token."""
    token = token.strip()
    while token and token[-1] in TRAILING_PUNCTUATION:
        # ')' is only stripped if the token has no unbalanced '('
        if token[-1] == ')' and token.count('(') > token.count(')'):
            break
        token = token[:-1]
        token = token.strip()
    return token


def extract_urls_from_text(text):
    """
    Extract valid URLs from arbitrary text.

    Handles:
      - multiple space-separated URLs per line
      - trailing punctuation (.,);:!?)]}"'> )
      - comment lines starting with '#'
      - blank lines
    Returns a deduplicated list preserving first-seen order.
    """
    seen = set()
    result = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        for token in line.split():
            if URL_REGEX.match(token):
                url = _clean_url(token)
                key = url.lower()
                if key not in seen:
                    seen.add(key)
                    result.append(url)
    return result


def extract_urls_from_file(filepath):
    """
    Read a .txt / .csv / .list file line-by-line and extract URLs.

    Non-UTF-8 bytes are decoded with errors='ignore' so a stray byte never
    aborts the whole parse. Returns a deduplicated URL list (first-seen order).
    """
    urls = []
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            urls.extend(extract_urls_from_text(line))
    # Deduplicate across lines, preserving order.
    seen = set()
    result = []
    for url in urls:
        key = url.lower()
        if key not in seen:
            seen.add(key)
            result.append(url)
    return result


def parse_urls_for_preview(urls):
    """
    Build a list of {url, valid} dicts for the preview dialog.

    A URL is considered structurally valid when it has a parseable netloc
    (http/https/ftp/ftps) or is a magnet: URI.
    """
    result = []
    for url in urls:
        parsed = urlparse(url)
        if url.lower().startswith('magnet:'):
            valid = bool(url) and 'urn:' in url.lower()
        else:
            valid = bool(parsed.scheme in ('http', 'https', 'ftp', 'ftps')) and bool(parsed.netloc)
        result.append({'url': url, 'valid': valid})
    return result
