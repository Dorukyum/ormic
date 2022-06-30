__all__ = ("Database",)

from typing import Any, Dict, Iterable, List, Optional, Type, TypeVar, Union

from aiosqlite import Connection, Row, connect

from .exceptions import NotConnected
from .model import Model

T = TypeVar("T")


class Database:
    """The handler for all transactions."""

    def __init__(
        self, *models: Type[Model], connection: Optional[Connection] = None
    ) -> None:
        self.models = []
        for model in models:
            self.add_model(model)
        self.connection = connection

        self.cache: Dict[Type[Model], List[Model]] = {}
        self.cache_config = {"on": False, "limit": None}

    def set_caching(self, *, on: bool, limit: int) -> None:
        self.cache_config["on"] = on
        self.cache_config["limit"] = limit

    def caching_on(self, model: Type[Model]) -> bool:
        return self.cache_config["on"] and model in self.cache

    def add_to_cache(self, model: Type[Model], *objects: Model) -> None:
        if count := (self.cache_config["limit"] - len(self.cache[model])) > 0:
            for object in objects[:count]:
                if object not in self.cache[model]:
                    self.cache[model].append(object)

    def add_model(self, model: Type[Model]) -> None:
        """Add a model to this database handler."""
        self.models.append(model)

    def model(self, cls: Type) -> Type:
        """A decorator to add a model to this database handler. It is suggested to use a subclass of `ormic.Model`."""
        if Model not in cls.__bases__:
            cls = type(
                cls.__name__, (cls, Model), {"__annotations__": cls.__annotations__}
            )
        cls._database = self
        self.add_model(cls)
        return cls

    async def connect(self, url: str, *, create_tables: bool = True) -> Connection:
        """Connect to an SQLite database."""
        self.connection = conn = await connect(url)
        if create_tables:
            await self.create_tables()
        return conn

    async def create_tables(self) -> None:
        """Create tables for the added models."""
        for model in self.models:
            await self.execute(f"CREATE TABLE IF NOT EXISTS {model.to_sql_table()}")

    async def execute(
        self,
        query: str,
        *,
        commit: bool = True,
        fetch: bool = False,
        fetch_one: bool = False,
    ) -> Optional[Union[Row, Iterable[Row]]]:
        """Execute an SQL query."""
        if self.connection is None:
            raise NotConnected()

        cursor = await self.connection.execute(query)
        if commit:
            await self.connection.commit()
        if fetch or fetch_one:
            return (await cursor.fetchall()) if fetch else (await cursor.fetchone())

    async def save(self, object: Model) -> None:
        """Save the given object into the database."""
        await self.execute(
            f"INSERT INTO {object.__tablename__} ({', '.join(object._fields.keys())}) VALUES {object.to_sql()})"
        )

    async def delete(self, object: Model, limit: Optional[int] = None) -> None:
        """Delete the given object from the database."""
        _limit: str = f" LIMIT {limit}" if limit is not None else ""
        await self.execute(
            f"DELETE FROM {object.__tablename__} WHERE ({object.to_sql_fields()}){_limit}"
        )

    async def update(self, object: Model) -> None:
        """Update the given object in the database."""
        await self.execute(
            f"UPDATE {object.__tablename__} SET {object.to_sql_fields(', ')}"
        )

    async def fetch_all(
        self, model: Type[Model], **values: Any
    ) -> Optional[List[Model]]:
        """Fetch all objects from the database that have the given values."""
        objects = [
            model(
                **{
                    k: v
                    for k, v in zip(
                        (item[0] for item in model._fields.items()),
                        data,
                    )
                }
            )
            for data in await self.execute(
                f"SELECT * FROM {model.__tablename__} WHERE {' AND '.join(f'{k} = {Model._sql_format(v)}' for k, v in values.items())}",
                commit=False,
                fetch=True,
            )  # type: ignore # the query will return Iterable[Row]
        ]
        if self.caching_on(model):
            self.add_to_cache(model, *objects)
        return objects

    async def fetch(self, model: Type[Model], **values: Any) -> Optional[Model]:
        """Fetch an object from the database that has the given values."""
        object: Model = model(
            **{
                k: v
                for k, v in zip(
                    (item[0] for item in model._fields.items()),
                    await self.execute(
                        f"SELECT * FROM {model.__tablename__} WHERE {' AND '.join(f'{k} = {Model._sql_format(v)}' for k, v in values.items())}",
                        commit=False,
                        fetch_one=True,
                    ),  # type: ignore # the query will return Row
                )
            }
        )
        if self.caching_on(model):
            self.add_to_cache(model, object)
        return object

    def get(self, model: Type[Model], **values: Any) -> Optional[Model]:
        """Get an object from the cache that has the given values."""
        if self.caching_on(model):
            for object in self.cache[model]:
                if all(
                    getattr(object, key, value) == value
                    for key, value in values.items()
                ):
                    return object

    async def get_or_fetch(self, model: Type[Model], **values: Any) -> Optional[Model]:
        """Get an object from the cache that has the given values. Tries to fetch from the database if none found."""
        if (object := self.get(model, **values)) is not None:
            return object

        return await self.fetch(model, **values)
