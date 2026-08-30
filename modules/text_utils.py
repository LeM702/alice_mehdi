import re

import nltk
from nltk import pos_tag
from nltk.corpus import stopwords, wordnet
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.tokenize import sent_tokenize, word_tokenize

try:
    from langdetect import LangDetectException, detect
except ImportError:
    detect = None

    class LangDetectException(Exception):
        pass


# télécharge les ressources NLTK une seule fois
def _ensure_nltk_data():
    resources = [
        "punkt", "punkt_tab",
        "stopwords",
        "wordnet", "omw-1.4",
        "averaged_perceptron_tagger", "averaged_perceptron_tagger_eng",
        "maxent_ne_chunker", "maxent_ne_chunker_tab",
        "words",
    ]
    for resource in resources:
        nltk.download(resource, quiet=True)


_ensure_nltk_data()

SUPPORTED_LANGUAGES = {
    "en": "english",
    "fr": "french",
    "de": "german",
    "es": "spanish",
    "it": "italian",
    "pt": "portuguese",
    "nl": "dutch",
}

_PG_START_RE = re.compile(
    r"\*\*\*\s*START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*",
    re.IGNORECASE,
)
_PG_END_RE = re.compile(
    r"\*\*\*\s*END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*",
    re.IGNORECASE,
)


def detect_language(text):
    if detect is None:
        return "en"
    try:
        lang = detect(text[:2000])
    except LangDetectException:
        return "en"
    return lang if lang in SUPPORTED_LANGUAGES else "en"


def get_stopwords(lang="en"):
    language = SUPPORTED_LANGUAGES.get(lang, "english")
    try:
        return set(stopwords.words(language))
    except OSError:
        return set(stopwords.words("english"))


def clean_text(text, lower=True):
    start_match = _PG_START_RE.search(text)
    end_match = _PG_END_RE.search(text)
    if start_match and end_match:
        text = text[start_match.end():end_match.start()]
    elif start_match:
        text = text[start_match.end():]

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\r\n?", "\n", text)

    if lower:
        text = text.lower()
    return text.strip()


def split_sentences(text, lang="en"):
    language = SUPPORTED_LANGUAGES.get(lang, "english")
    try:
        return sent_tokenize(text, language=language)
    except LookupError:
        return sent_tokenize(text, language="english")


# une section = un chapitre (regex CHAPTER/PART/BOOK)
_SECTION_RE = re.compile(
    r"\n\s*(?:CHAPTER|CHAPITRE|KAPITEL|CAPITOLO|CAP[IÍ]TULO|BOOK|PART)\s+[IVXLCDM\d]+\b",
    re.IGNORECASE,
)

_lemmatizer = WordNetLemmatizer()
_stemmer = PorterStemmer()


def split_sections(text):
    parts = [p.strip() for p in _SECTION_RE.split(text) if p.strip()]
    return parts if len(parts) > 1 else [text.strip()]


def _wordnet_pos(tag):
    if tag.startswith("V"):
        return wordnet.VERB
    if tag.startswith("J"):
        return wordnet.ADJ
    if tag.startswith("R"):
        return wordnet.ADV
    return wordnet.NOUN


def normalize_tokens(tokens, method="lemmatize"):
    if method == "stem":
        return [_stemmer.stem(t) for t in tokens]

    # tag par paquets de 200 tokens, pas tout le livre d'un coup
    chunk_size = 200
    normalized = []
    for i in range(0, len(tokens), chunk_size):
        chunk = tokens[i:i + chunk_size]
        for token, tag in pos_tag(chunk):
            normalized.append(_lemmatizer.lemmatize(token.lower(), pos=_wordnet_pos(tag)))
    return normalized


NARRATIVE_STOPWORDS = {
    "say", "go", "get", "come", "look", "seem", "feel", "tell", "ask",
    "reply", "cry", "turn", "find", "take", "make", "see", "think",
    "must", "shall", "begin", "could", "would",
    "upon", "away", "back", "round", "much", "well", "quite", "rather",
    "every", "never", "always", "still", "even", "also", "way", "time",
    "thing", "good", "us", "them", "him", "her",
}


def tokenize_text(text, lang="en", remove_stop=True, remove_punct=True,
                   lemmatize=False, filter_narrative=False):
    tokens = word_tokenize(text)

    if remove_punct:
        tokens = [t for t in tokens if any(c.isalnum() for c in t)]
    if remove_stop:
        stops = get_stopwords(lang)
        tokens = [t for t in tokens if t.lower() not in stops]

    if lemmatize:
        tokens = normalize_tokens(tokens, method="lemmatize")

    if filter_narrative:
        tokens = [t for t in tokens if t not in NARRATIVE_STOPWORDS]

    return tokens
