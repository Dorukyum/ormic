__all__ = (
    "OrmicException",
    "BadValue",
    "FieldDoesNotExist",
    "NotConnected",
)


from typing import Optional


class OrmicException(BaseException):
    """Base class for all ormic exceptions."""

    text: str = ""

    def __init__(self, text: Optional[str] = None) -> None:
        super().__init__(text or self.text)


class BadValue(OrmicException):
    """Raised when a value passed to a field is of a wrong type."""

    def __init__(self, field_name: str, expected_type: str) -> None:
        super().__init__(
            "received wrong value type for field {}, expected {}".format(
                field_name, expected_type
            )
        )


class FieldDoesNotExist(OrmicException):
    """Raised when a value has been set to a non-existent field."""

    def __init__(self, field_name: str) -> None:
        super().__init__("{} is not an existent field".format(field_name))


class NotConnected(OrmicException):
    """Raised when the database handler isn't connected to a database."""

    text = "This database handler isn't connected to a database."
