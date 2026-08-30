#!/usr/bin/env python3
import argparse
import sys

from modules.card import get_card
from modules.entities import get_entities
from modules.lexdiv import get_lexdiv
from modules.similar import get_similar
from modules.summarize import get_summarize
from modules.topics import get_topics

TASKS = {
    "lexdiv": get_lexdiv,
    "topics": get_topics,
    "entities": get_entities,
    "summarize": get_summarize,
    "similar": get_similar,
    "card": get_card,
}


def build_parser():
    parser = argparse.ArgumentParser(
        prog="bookworm.py",
        description="Transforme un livre Project Gutenberg en book card structurée.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--lexdiv", type=int, metavar="ID",
                        help="diversité lexicale du livre ID")
    group.add_argument("--topics", type=int, metavar="ID",
                        help="mots-clés du topic principal par section du livre ID")
    group.add_argument("--entities", type=int, metavar="ID",
                        help="personnages et lieux cités dans le livre ID")
    group.add_argument("--summarize", type=int, metavar="ID",
                        help="résumé court du livre ID")
    group.add_argument("--similar", type=int, metavar="ID",
                        help="5 livres les plus proches du livre ID")
    group.add_argument("--card", type=int, metavar="ID",
                        help="book card complète pour le livre ID")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    task_name, book_id = next(
        (name, value) for name, value in vars(args).items() if value is not None
    )

    if book_id <= 0:
        print(f"Error: book ID must be a positive integer, got {book_id}.")
        return 1

    try:
        result = TASKS[task_name](book_id)
    except Exception as exc:
        print(f"Error: --{task_name} failed for book {book_id}: {exc}")
        return 1

    if result is None:
        print(f"Error: book {book_id} could not be retrieved or processed "
              f"(check the ID and your network connection).")
        return 1

    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
