__all__ = ("Field", "sql_type", "python_type")


from collections import namedtuple
from datetime import datetime
from typing import Any, Dict, Union

Datatype = namedtuple("Datatype", ("python", "sql"))
DATATYPES = (
    Datatype(str, ("TEXT", "CHAR")),
    Datatype(int, ("INTEGER", "BIGINT")),
    Datatype(float, ("FLOAT",)),
    Datatype(datetime, ("DATETIME",)),
)


def sql_type(python_type: type) -> str:
    for datatype in DATATYPES:
        if datatype.python == python_type:
            return datatype.sql[0]
    raise Exception(f"received invalid type {python_type.__name__}")


def python_type(sql_type: str) -> type:
    for datatype in DATATYPES:
        if sql_type in datatype.sql:
            return datatype.python
    raise Exception(f"received invalid SQL type {sql_type}")


class Field:
    def __init__(self, name: str, field_type: Union[type, str], default: Any) -> None:
        self.name = name

        if isinstance(field_type, str):
            self.type = python_type(field_type)
            self.sql_type = field_type
        else:
            self.sql_type = sql_type(field_type)
            self.type = field_type

        self.default = default

    def to_python(self, data: str) -> Any:
        return self.type(data)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "default": self.default,
        }

    def to_sql(self) -> str:
        return f"{self.name} {self.sql_type}"
