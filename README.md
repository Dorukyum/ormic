<center>
    <h1>ormic</h1>
    <h3>A simple, asynchronous python ORM for SQLite databases</h3>
</center>

## Installation
```sh
# stable
$ pip install ormic

# unstable
$ pip install git+https://github.com/Dorukyum/ormic
```

## Quickstart
```py
from ormic import Database, Model

db = Database()

# create a model
@db.model
class Point(Model):
    name: str
    x: int
    y: int = 5  # default value

# connect to a database
await db.connect("database.db")
```

## Database Actions
```py
# create an object
point = Point(name="A", x=5, y=10)
await point.save()

# fetch objects from the database
point_named_A: Point | None                = await Point.fetch(name="A")
list_of_points_named_A: list[Point] | None = await Point.fetch_all(name="A")

# update an object
await point.update(y=15)
# or
point.y = 15
await point.update()

# delete an object
await point.delete()
```

## Caching
```py
# turn caching on
# setting limit to 20 will only cache the last fetched 20 objects
# this parameter defaults to None, caching all fetched objects
database.set_caching(on=True, limit=20)

# get the object from the cache
# will fetch from the database if no matches found
point_named_A = await Point.get_or_fetch(name="A")
```