import json
import os

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from modules.downloader import get_book_text
from modules.text_utils import clean_text, tokenize_text

CACHE_DIR = "cache"

# collection fixe donnée dans le sujet
COLLECTION = [
    (11, "Alice's Adventures in Wonderland", "Children / Young Adult"),
    (12, "Through the Looking-Glass", "Children / Young Adult"),
    (16, "Peter Pan", "Children / Young Adult"),
    (55, "The Wonderful Wizard of Oz", "Children / Young Adult"),
    (113, "The Secret Garden", "Children / Young Adult"),
    (120, "Treasure Island", "Children / Young Adult"),
    (236, "The Jungle Book", "Children / Young Adult"),
    (108, "The Return of Sherlock Holmes", "Crime, Mystery & Thriller"),
    (834, "The Memoirs of Sherlock Holmes", "Crime, Mystery & Thriller"),
    (863, "The Mysterious Affair at Styles", "Crime, Mystery & Thriller"),
    (1661, "The Adventures of Sherlock Holmes", "Crime, Mystery & Thriller"),
    (61262, "Poirot Investigates", "Crime, Mystery & Thriller"),
    (69087, "The Murder of Roger Ackroyd", "Crime, Mystery & Thriller"),
    (70114, "The Big Four", "Crime, Mystery & Thriller"),
    (35, "The Time Machine", "Science-Fiction & Fantasy"),
    (36, "The War of the Worlds", "Science-Fiction & Fantasy"),
    (84, "Frankenstein; Or, The Modern Prometheus", "Science-Fiction & Fantasy"),
    (159, "The Island of Doctor Moreau", "Science-Fiction & Fantasy"),
    (164, "Twenty Thousand Leagues under the Sea", "Science-Fiction & Fantasy"),
    (345, "Dracula", "Science-Fiction & Fantasy"),
    (68283, "The Call of Cthulhu", "Science-Fiction & Fantasy"),
]
TITLE_BY_ID = {book_id: title for book_id, title, _ in COLLECTION}


def _load_corpus():
    cache_path = os.path.join(CACHE_DIR, "similar_corpus.json")
    os.makedirs(CACHE_DIR, exist_ok=True)
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)

    corpus = {}
    for book_id, _, _ in COLLECTION:
        text = get_book_text(book_id)
        if text is None:
            print(f"Warning: could not download book {book_id}, "
                  f"it will be excluded from --similar.")
            continue
        tokens = tokenize_text(clean_text(text, lower=True), lang="en",
                                remove_stop=True, remove_punct=True,
                                lemmatize=True)
        corpus[str(book_id)] = " ".join(tokens)

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(corpus, f)
    return corpus


def get_similar(book_id):
    if book_id not in TITLE_BY_ID:
        print(f"Error: book {book_id} is not part of the --similar "
              f"reference collection.")
        return None

    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f"{book_id}_similar.json")
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)

    corpus = _load_corpus()
    ids = [int(k) for k in corpus.keys()]
    if book_id not in ids:
        print(f"Error: could not download book {book_id} to compute similarity.")
        return None
    texts = [corpus[str(i)] for i in ids]

    vectorizer = TfidfVectorizer(max_features=15000, ngram_range=(1, 2),
                                  sublinear_tf=True, min_df=2)
    tfidf = vectorizer.fit_transform(texts)

    target_idx = ids.index(book_id)
    scores = cosine_similarity(tfidf[target_idx], tfidf)[0]
    ranked = sorted(
        ((ids[i], scores[i]) for i in range(len(ids)) if ids[i] != book_id),
        key=lambda pair: pair[1],
        reverse=True,
    )
    result = [TITLE_BY_ID[bid] for bid, _ in ranked[:5]]

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(result, f)
    return result
