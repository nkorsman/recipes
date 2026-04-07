import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

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


def get_user_id(username):
    sql = "SELECT id FROM Users WHERE username = ?"
    result = database.query_db(sql, [username], one=True)
    return result[0] if result else None


def check_password(user_id, password):
    sql = "SELECT password_hash FROM Users WHERE id = ?"
    result = database.query_db(sql, [user_id], one=True)
    if result is None:
        return False

    return check_password_hash(result[0], password)
