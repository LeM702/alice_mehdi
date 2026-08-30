import json
import os
from collections import Counter

from modules.downloader import get_book_language, get_book_text
from modules.text_utils import clean_text, tokenize_text

CACHE_DIR = "cache"


def get_lexdiv(book_id):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f"{book_id}_lexdiv.json")
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)

    text = get_book_text(book_id)
    if text is None:
        return None
    lang = get_book_language(book_id)

    # pas de lemmatisation, on veut le vrai vocabulaire de l'auteur
    cleaned = clean_text(text, lower=True)
    tokens = tokenize_text(cleaned, lang=lang, remove_stop=False,
                            remove_punct=True, lemmatize=False)
    tokens = [t for t in tokens if not t.isnumeric()]

    tok = len(tokens)
    if tok == 0:
        result = {"tok": 0, "typ": 0, "hap": 0, "ttr": 0.0, "mwl": 0.0, "mwf": 0.0}
    else:
        freq = Counter(tokens)
        typ = len(freq)
        hap = sum(1 for count in freq.values() if count == 1)
        result = {
            "tok": tok,
            "typ": typ,
            "hap": hap,
            "ttr": round(typ / tok, 4),
            "mwl": round(sum(len(t) for t in tokens) / tok, 4),
            "mwf": round(tok / typ, 4),
        }

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(result, f)
    return result
