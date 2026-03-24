import sqlite3

from flask import g


def get_db():
    db = getattr(g, "db", None)
    if db is None:
        db = g.db = sqlite3.connect("database.db")
    return db


def close_db(exception):
    db = getattr(g, "db", None)
    if db is not None:
        db.close()
