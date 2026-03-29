import sqlite3
from functools import wraps

from flask import Flask, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

import config
import database
import recipe

app = Flask(__name__)
app.teardown_appcontext(database.close_db)
app.secret_key = config.secret_key


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return "ERROR: You are not logged in"
        return f(*args, **kwargs)

    return decorated_function


@app.route("/")
def index():
    recipes = recipe.get_recipes()
    return render_template("index.html", recipes=recipes)


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form["username"]
    password = request.form["password"]

    sql = "SELECT id, password_hash FROM Users WHERE username = ?"
    row = database.query_db(sql, [username], one=True)
    if row is None:
        return "ERROR: incorrect username or password"

    user_id = row[0]
    password_hash = row[1]

    if check_password_hash(password_hash, password):
        session["user_id"] = user_id
        return redirect("/")

    return "ERROR: incorrect username or password"


@app.route("/logout")
@login_required
def logout():
    del session["user_id"]
    return redirect("/")


@app.route("/create-user", methods=["POST"])
def create_user():
    username = request.form["username"].strip()
    password1 = request.form["password1"]
    password2 = request.form["password2"]

    if password1 != password2:
        return "ERROR: Passwords don't match"
    if not username or len(username) > 40:
        return "ERROR: invalid username"
    if len(password1) < 8 or len(password1) > 100:
        return "ERROR: invalid password"

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


@app.route("/create-recipe")
@login_required
def create_recipe():
    author_id = session["user_id"]
    title = "Untitled recipe"

    recipe_id = recipe.new_recipe(author_id, title)

    return redirect(f"/edit/{recipe_id}")


@app.route("/delete-recipe", methods=["POST"])
@login_required
def delete_recipe():
    recipe_id = request.form["recipe_id"]
    author_id = recipe.get_recipe_author(recipe_id)
    if author_id is None:
        return "ERROR: Recipe does not exist"
    if author_id != session["user_id"]:
        return "ERROR: You do not have permission to perform this action"

    recipe.delete_recipe(recipe_id)
    return redirect("/")


@app.route("/create-ingredient", methods=["POST"])
@login_required
def create_ingredient():
    recipe_id = request.form["recipe_id"]
    author_id = recipe.get_recipe_author(recipe_id)
    if author_id is None:
        return "ERROR: Recipe does not exist"
    if author_id != session["user_id"]:
        return "ERROR: You do not have permission to perform this action"

    content = request.form["content"].strip()
    if not content or len(content) > 100:
        return "ERROR: invalid ingredient"

    ingredient_number = recipe.next_ingredient_number(recipe_id)
    recipe.new_ingredient(recipe_id, ingredient_number, content)

    return redirect(f"/edit/{recipe_id}")


@app.route("/delete-ingredient", methods=["POST"])
@login_required
def delete_ingredient():
    recipe_id = request.form["recipe_id"]
    author_id = recipe.get_recipe_author(recipe_id)
    if author_id is None:
        return "ERROR: Recipe does not exist"
    if author_id != session["user_id"]:
        return "ERROR: You do not have permission to perform this action"

    ingredient_id = request.form["ingredient_id"]
    recipe.delete_ingredient(ingredient_id)

    return redirect(f"/edit/{recipe_id}")


@app.route("/create-instruction", methods=["POST"])
@login_required
def create_instruction():
    recipe_id = request.form["recipe_id"]
    author_id = recipe.get_recipe_author(recipe_id)
    if author_id is None:
        return "ERROR: Recipe does not exist"
    if author_id != session["user_id"]:
        return "ERROR: You do not have permission to perform this action"

    content = request.form["content"].strip()
    if not content or len(content) > 2000:
        return "ERROR: invalid instruction step"

    instruction_number = recipe.next_instruction_number(recipe_id)
    recipe.new_instruction(recipe_id, instruction_number, content)

    return redirect(f"/edit/{recipe_id}")


@app.route("/delete-instruction", methods=["POST"])
@login_required
def delete_instruction():
    recipe_id = request.form["recipe_id"]
    author_id = recipe.get_recipe_author(recipe_id)
    if author_id is None:
        return "ERROR: Recipe does not exist"
    if author_id != session["user_id"]:
        return "ERROR: You do not have permission to perform this action"

    instruction_id = request.form["instruction_id"]
    recipe.delete_instruction(instruction_id)

    return redirect(f"/edit/{recipe_id}")


@app.route("/recipe/<int:recipe_id>")
def show_recipe(recipe_id):
    r = recipe.get_recipe(recipe_id)
    if r is None:
        return "ERROR: Recipe not found"
    ingredients = recipe.get_ingredients(recipe_id)
    instructions = recipe.get_instructions(recipe_id)

    return render_template(
        "recipe.html", recipe=r, ingredients=ingredients, instructions=instructions
    )


@app.route("/edit/<int:recipe_id>", methods=["GET", "POST"])
@login_required
def edit_recipe(recipe_id):
    author_id = recipe.get_recipe_author(recipe_id)
    if author_id is None:
        return "ERROR: Recipe does not exist"
    if author_id != session["user_id"]:
        return "ERROR: You do not have permission to perform this action"

    if request.method == "POST":
        title = request.form["title"].strip()
        if not title or len(title) > 100:
            return "ERROR: Invalid recipe title"
        recipe.update_recipe(recipe_id, title)

    r = recipe.get_recipe(recipe_id)
    ingredients = recipe.get_ingredients(recipe_id)
    instructions = recipe.get_instructions(recipe_id)

    return render_template(
        "edit.html", recipe=r, ingredients=ingredients, instructions=instructions
    )
