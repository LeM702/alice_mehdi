import json
import os

from sumy.nlp.tokenizers import Tokenizer
from sumy.parsers.plaintext import PlaintextParser
from sumy.summarizers.text_rank import TextRankSummarizer

from modules.downloader import get_book_language, get_book_text
from modules.text_utils import SUPPORTED_LANGUAGES, clean_text

CACHE_DIR = "cache"
SUMMARY_SENTENCES = 6


def get_summarize(book_id):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f"{book_id}_summarize.json")
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)

    text = get_book_text(book_id)
    if text is None:
        return None
    lang = get_book_language(book_id)

    cleaned = clean_text(text, lower=False)

    language_name = SUPPORTED_LANGUAGES.get(lang, "english")
    parser = PlaintextParser.from_string(cleaned, Tokenizer(language_name))
    summarizer = TextRankSummarizer()
    sentences = summarizer(parser.document, sentences_count=SUMMARY_SENTENCES)

    result = " ".join(str(s) for s in sentences)

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(result, f)
    return result
