__all__ = ("Model",)

from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Type,
)

from .exceptions import BadValue, FieldDoesNotExist
from .field import Field

if TYPE_CHECKING:
    from .database import Database


class Model:
    """The base class for all database models."""

    _database: Optional["Database"] = None
    _fields: Dict[str, Field] = {}
    __tablename__: str

    def __init_subclass__(cls) -> None:
        for name, type in cls.__annotations__.items():
            default = getattr(cls, name, None)
            field = (
                default if isinstance(default, Field) else Field(name, type, default)
            )
            cls._fields[name] = field

        cls.__tablename__ = getattr(cls, "__tablename__", cls.__name__)

    @classmethod
    def to_dict(cls) -> Dict[str, List[Dict[str, Any]]]:
        return {"fields": [field.to_dict() for field in cls._fields.values()]}

    @classmethod
    def to_sql_table(cls) -> str:
        """Returns the SQL string for this model. Example: `USERS (id INTEGER, name TEXT)`"""
        return f"{cls.__tablename__} ({', '.join(field.to_sql() for field in cls._fields.values())})"

    def __init__(self, **values) -> None:
        self.set_values(**values)

    @property
    def fields(self) -> Iterable[Field]:
        return self._fields.values()

    @property
    def values(self) -> Tuple[Any]:
        return tuple(self._get_value(field) for field in self.fields)

    @property
    def database(self) -> "Database":
        """Returns the database this model was added to."""
        if self._database is not None:
            return self._database
        raise Exception("this model has not been added to any databases")

    @classmethod
    def _get_database(cls) -> "Database":
        """Returns the database this model was added to."""
        if cls._database is not None:
            return cls._database
        raise Exception("this model has not been added to any databases")

    def __eq__(self, other: "Model") -> bool:
        return isinstance(other, type(self)) and self.values == other.values

    def _get_value(self, field) -> Any:
        """Return the value of this object for the provided field."""
        return getattr(self, field.name, field.default)

    @staticmethod
    def _sql_format(value: Any) -> str:
        return f"'{value}'" if isinstance(value, str) else str(value)

    def to_sql(self) -> str:
        """Returns the SQL string for the values of this object. Example: `(12345, 'Dorukyum')`"""
        return f"({', '.join((self._sql_format(self._get_value(field)) for field in self.fields))}"

    def to_sql_fields(self, joiner: str = " AND ") -> str:
        return joiner.join(
            f"{field.name} = {self._sql_format(self._get_value(field))}"
            for field in self.fields
        )

    async def save(self) -> None:
        """Saves the object to the database."""
        await self.database.save(self)

    def set_values(self, **new_values) -> None:
        for name, value in new_values.items():
            if field := self._fields.get(name):
                if isinstance(value, field.type):
                    setattr(self, name, value)
                else:
                    raise BadValue(field.name, field.type.__name__)
            else:
                raise FieldDoesNotExist(name)

    async def update(self, *, save: bool = True, **new_values):
        """Updates the object. You can also use :attr:`.set_values` to update the object in-place.

        Parameters
        ----------
        save: bool
            Whether to update the database. Defaults to ``True``.
        """
        self.set_values(**new_values)
        if save:
            await self.database.update(self)

    async def delete(self, limit: Optional[int] = None) -> None:
        """Delete the object from the database."""
        await self.database.delete(self, limit)

    @classmethod
    async def fetch(cls: Type["Model"], **values) -> Optional["Model"]:
        """Fetch an object from the database that has the given values."""
        database = cls._get_database()
        return await database.fetch(cls, **values)

    @classmethod
    async def fetch_all(cls: Type["Model"], **values) -> Optional[List["Model"]]:
        """Fetch all objects from the database that have the given values."""
        database = cls._get_database()
        return await database.fetch_all(cls, **values)

    @classmethod
    def get(cls: Type["Model"], **values) -> Optional["Model"]:
        """Get an object from the cache that has the given values."""
        database = cls._get_database()
        return database.get(cls, **values)

    @classmethod
    async def get_or_fetch(cls: Type["Model"], **values) -> Optional["Model"]:
        """Get an object from the cache that has the given values. Tries to fetch from the database if none found."""
        database = cls._get_database()
        return await database.get_or_fetch(cls, **values)
