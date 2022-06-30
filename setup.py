from setuptools import setup

classifiers = [
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
]

with open("README.md", encoding="utf-8") as f:
    readme = f.read()

setup(
    name="ormic",
    packages=["ormic"],
    version="1.0.0",
    license="MIT",
    description="A simple, asynchronous python ORM for SQLite databases",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Dorukyum",
    url="https://github.com/Dorukyum/ormic",
    keywords="database, ORM",
    install_requires=["aiosqlite"],
    classifiers=classifiers,
    project_urls={"Source": "https://github.com/Dorukyum/ormic"},
)
