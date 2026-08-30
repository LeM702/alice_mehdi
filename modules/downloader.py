import json
import os
import time

import requests

GUTENDEX_URL = "https://gutendex.com/books/{id}"
MAX_RETRIES = 3
RETRY_DELAY = 2
REQUEST_TIMEOUT = 30

CACHE_DIR = "cache"
BOOKS_DIR = "books"


def _get(url):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                return response
            print(f"Error: HTTP {response.status_code} for {url} "
                  f"(attempt {attempt}/{MAX_RETRIES}).")
        except requests.exceptions.RequestException as exc:
            print(f"Error: network error for {url} ({exc}) "
                  f"(attempt {attempt}/{MAX_RETRIES}).")
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY * attempt)
    return None


def _cache_path(book_id, suffix):
    return os.path.join(CACHE_DIR, f"{book_id}_{suffix}.json")


def get_book_info(book_id):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = _cache_path(book_id, "info")
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)

    response = _get(GUTENDEX_URL.format(id=book_id))
    if response is None:
        return None
    data = response.json()

    languages = data.get("languages") or ["en"]
    result = {
        "id": str(book_id),
        "title": data.get("title", ""),
        "authors": ", ".join(a["name"] for a in data.get("authors", [])),
        "bookshelves": "; ".join(data.get("bookshelves", [])),
        "language": languages[0],
    }

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(result, f)
    return result


def get_book_text(book_id):
    os.makedirs(BOOKS_DIR, exist_ok=True)
    book_path = os.path.join(BOOKS_DIR, f"{book_id}.txt")
    if os.path.exists(book_path):
        with open(book_path, encoding="utf-8") as f:
            return f.read()

    response = _get(GUTENDEX_URL.format(id=book_id))
    if response is None:
        return None
    data = response.json()

    formats = data.get("formats", {})
    text_url = (
        formats.get("text/plain; charset=utf-8")
        or formats.get("text/plain; charset=us-ascii")
        or next((url for fmt, url in formats.items()
                  if fmt.startswith("text/plain")), None)
    )
    if not text_url:
        print(f"Error: no plain text format available for book {book_id}.")
        return None

    book_response = _get(text_url)
    if book_response is None:
        return None

    book_response.encoding = book_response.encoding or "utf-8"
    with open(book_path, "w", encoding="utf-8") as f:
        f.write(book_response.text)
    return book_response.text


def get_book_language(book_id):
    info = get_book_info(book_id)
    return info["language"] if info else "en"
