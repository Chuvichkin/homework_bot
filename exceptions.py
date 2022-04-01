class APIAnswerInvalidException(Exception):
    """Исключение, если получен неправильный ответ API."""

    pass


class APIWrongStatusException(Exception):
    """Исключение, если API вернул некорректный статус."""

    pass


class MissingTokenException(Exception):
    """Исключение, если отсутствуют обязательные для работы токены."""

    pass
