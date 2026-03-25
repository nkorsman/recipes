import sqlite3

from flask import g


def get_db():
    db = getattr(g, "db", None)
    if db is None:
        db = g.db = sqlite3.connect("database.db")
        db.execute("PRAGMA foreign_keys = ON")
        db.row_factory = sqlite3.Row
    return db


def query_db(query, args=(), one=False):
    result = get_db().execute(query, args)
    rows = result.fetchall()
    return (rows[0] if rows else None) if one else rows


def close_db(exception):
    db = getattr(g, "db", None)
    if db is not None:
        db.close()
