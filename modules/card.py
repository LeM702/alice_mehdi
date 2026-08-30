from modules.downloader import get_book_info
from modules.entities import get_entities
from modules.lexdiv import get_lexdiv
from modules.similar import get_similar
from modules.summarize import get_summarize
from modules.topics import get_topics


def get_card(book_id):
    info = get_book_info(book_id)
    if info is None:
        return None

    lexdiv = get_lexdiv(book_id)
    topics = get_topics(book_id)
    entities = get_entities(book_id)
    summary = get_summarize(book_id)
    similar = get_similar(book_id)

    return {
        "info": {
            "id": str(info["id"]),
            "authors": str(info["authors"]),
            "bookshelves": str(info["bookshelves"]),
        },
        "lexdiv": lexdiv,
        "topics": topics,
        "entities": entities,
        "summary": summary,
        "similar": similar,
    }
