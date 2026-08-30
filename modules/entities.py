import json
import os
from collections import Counter

from nltk import pos_tag
from nltk.chunk import ne_chunker
from nltk.tokenize import word_tokenize

from modules.downloader import get_book_language, get_book_text
from modules.text_utils import clean_text, split_sentences

CACHE_DIR = "cache"

MIN_MENTIONS = 2

FALSE_POSITIVES = {
    "gutenberg", "project", "chapter", "ebook", "book", "part",
    "illustration", "contents", "appendix", "preface", "introduction",
    "mr", "mrs", "miss", "sir", "lord", "lady",
}

# charger le chunker une seule fois : ne_chunk() le recharge à chaque
# appel, ça mettait 13min sur un livre entier au lieu de 7s
_ne_chunker = None


def _get_chunker():
    global _ne_chunker
    if _ne_chunker is None:
        _ne_chunker = ne_chunker()
    return _ne_chunker


def _extract(text, lang="en"):
    if lang != "en":
        print(f"Warning: named entity recognition is only trained for "
              f"English; results for '{lang}' may be less accurate.")

    chunker = _get_chunker()
    characters, locations = Counter(), Counter()
    for sentence in split_sentences(text, lang):
        tagged = pos_tag(word_tokenize(sentence))
        for chunk in chunker.parse(tagged):
            if not hasattr(chunk, "label"):
                continue
            name = " ".join(token for token, _ in chunk).strip()
            if len(name) <= 1 or name.lower() in FALSE_POSITIVES:
                continue
            if chunk.label() == "PERSON":
                characters[name] += 1
            elif chunk.label() in ("GPE", "LOCATION"):
                locations[name] += 1
    return characters, locations


def _dedupe_and_filter(counter, min_mentions):
    merged = Counter()
    canonical_form = {}
    for name, freq in counter.items():
        key = name.lower()
        merged[key] += freq
        if freq > counter.get(canonical_form.get(key, ""), 0):
            canonical_form[key] = name
    return [canonical_form[key] for key, freq in merged.most_common() if freq >= min_mentions]


def get_entities(book_id):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f"{book_id}_entities.json")
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)

    text = get_book_text(book_id)
    if text is None:
        return None
    lang = get_book_language(book_id)

    # casse gardée : aide le NER à repérer les noms propres
    cleaned = clean_text(text, lower=False)
    characters, locations = _extract(cleaned, lang)

    result = {
        "characters": _dedupe_and_filter(characters, MIN_MENTIONS),
        "locations": _dedupe_and_filter(locations, MIN_MENTIONS),
    }

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(result, f)
    return result