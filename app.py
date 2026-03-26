import sqlite3

from flask import Flask, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

import config
import database

app = Flask(__name__)
app.teardown_appcontext(database.close_db)
app.secret_key = config.secret_key


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form["username"]
    password = request.form["password"]

    sql = "SELECT password_hash FROM Users WHERE username = ?"
    row = database.query_db(sql, [username], one=True)
    if row is None:
        return "ERROR: incorrect username or password"

    password_hash = row[0]

    if check_password_hash(password_hash, password):
        session["username"] = username
        return redirect("/")

    return "ERROR: incorrect username or password"


@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")


@app.route("/create-user", methods=["POST"])
def create_user():
    username = request.form["username"]
    password1 = request.form["password1"]
    password2 = request.form["password2"]

    if password1 != password2:
        return "ERROR: Passwords don't match"

    password_hash = generate_password_hash(password1)
    print(1)

    try:
        db = database.get_db()
        sql = "INSERT INTO Users (username, password_hash) VALUES (?, ?)"
        db.execute(sql, [username, password_hash])
        db.commit()
    except sqlite3.IntegrityError:
        return "ERROR: Username taken"

    return f"User {username} created"


@app.route("/create-recipe", methods=["POST"])
def create_recipe():
    username = session["username"]

    sql = "SELECT id FROM Users WHERE username = ?"
    row = database.query_db(sql, [username], one=True)
    if row is None:
        return "ERROR: User not found"

    author_id = row[0]

    title = request.form["title"]

    db = database.get_db()
    sql = "INSERT INTO Recipes (title, author_id) VALUES (?, ?)"
    db.execute(sql, [title, author_id])
    db.commit()

    return "Recipe created successfully"


@app.route("/recipe/<int:recipe_id>")
def show_recipe(recipe_id):
    sql = "SELECT title FROM Recipes WHERE id = ?"
    row = database.query_db(sql, [recipe_id], one=True)
    if row is None:
        return "ERROR: Recipe not found"
    title = row[0]

    return render_template("recipe.html", recipe_title=title)
