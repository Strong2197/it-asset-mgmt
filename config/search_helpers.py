from collections.abc import Iterable


def filter_by_text_query(objects: Iterable, query: str, text_builder):
    query_cf = (query or '').casefold()
    if not query_cf:
        return list(objects)

    matched = []
    for obj in objects:
        text = (text_builder(obj) or '').casefold()
        if query_cf in text:
            matched.append(obj)
    return matched
