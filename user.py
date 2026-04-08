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


def validate_password(password1, password2):
    errors = []
    if password1 != password2:
        errors.append("The passwords you've entered don't match.")
    if len(password1) < 8:
        errors.append("Password must be at least 8 characters")
    if len(password1) > 100:
        errors.append("Password must not be longer than 100 characters.")
    return errors


def parse_username(input):
    username = input.strip()
    errors = []
    if not username.isalnum():
        errors.append("Username must consist of only letters and numbers.")
    if len(username) > 20:
        errors.append("Username must not be longer than 20 characters.")
    return username, errors


def check_password(user_id, password):
    sql = "SELECT password_hash FROM Users WHERE id = ?"
    result = database.query_db(sql, [user_id], one=True)
    if result is None:
        return False

    return check_password_hash(result[0], password)
