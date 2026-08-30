import json
import logging
import os

from gensim import corpora
from gensim.models import LdaModel

from modules.downloader import get_book_language, get_book_text
from modules.text_utils import clean_text, split_sections, tokenize_text

logging.getLogger("gensim").setLevel(logging.WARNING)

CACHE_DIR = "cache"
MIN_TOKENS_PER_SECTION = 30
MAX_TOPICS = 8
LDA_PASSES = 10


def get_topics(book_id):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f"{book_id}_topics.json")
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            # JSON garde que des clés string, on reconvertit en int
            return {int(k): v for k, v in json.load(f).items()}

    text = get_book_text(book_id)
    if text is None:
        return None
    lang = get_book_language(book_id)

    sections = split_sections(clean_text(text, lower=False))
    section_tokens = [
        tokenize_text(clean_text(section, lower=True), lang=lang,
                       remove_stop=True, remove_punct=True,
                       lemmatize=True, filter_narrative=True)
        for section in sections
    ]
    section_tokens = [tokens for tokens in section_tokens if len(tokens) >= MIN_TOKENS_PER_SECTION]
    if not section_tokens:
        return None

    dictionary = corpora.Dictionary(section_tokens)
    dictionary.filter_extremes(no_below=2, no_above=0.85)
    if len(dictionary) == 0:
        dictionary = corpora.Dictionary(section_tokens)

    corpus = [dictionary.doc2bow(tokens) for tokens in section_tokens]
    if not any(corpus):
        return None

    num_topics = min(MAX_TOPICS, len(section_tokens))
    model = LdaModel(
        corpus=corpus,
        id2word=dictionary,
        num_topics=num_topics,
        passes=LDA_PASSES,
        random_state=42,
        alpha="auto",
        eta="auto",
    )

    # une entrée par section : chaque section prend son topic dominant
    result = {}
    for section_num, bow in enumerate(corpus, start=1):
        topic_weights = model.get_document_topics(bow)
        main_topic_id = max(topic_weights, key=lambda tw: tw[1])[0] if topic_weights else 0
        result[section_num] = [word for word, _ in model.show_topic(main_topic_id, topn=10)]

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(result, f)
    return result
