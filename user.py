import sqlite3

from werkzeug.security import generate_password_hash

import database


def new_user(username, password):
    db = database.get_db()
    password_hash = generate_password_hash(password)
    sql = "INSERT INTO Users (username, password_hash) VALUES (?, ?)"
    try:
        result = db.execute(sql, [username, password_hash])
        db.commit()
    except sqlite3.IntegrityError:
        return None
    return result.lastrowid
