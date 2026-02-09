def format_topics_list(topics: list) -> str:
    """Форматирует список тем для отображения"""
    return "\n".join([f"{i + 1}. {t}" for i, t in enumerate(topics)])
