from functools import wraps

from flask import Flask, abort, flash, redirect, render_template, request, session

import config
import database
import recipe
import tag
import user

app = Flask(__name__)
app.teardown_appcontext(database.close_db)
app.secret_key = config.secret_key


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return abort(401, "You must be logged in to perform this action.")
        return f(*args, **kwargs)

    return decorated_function


@app.errorhandler(404)
@app.errorhandler(403)
@app.errorhandler(401)
def error(e):
    return render_template("error.html", error=e)


@app.route("/")
def index():
    recipes = recipe.get_recipes()
    return render_template("index.html", recipes=recipes)


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        abort(403, "You must log out first before you can register a new account.")
    if request.method == "GET":
        return render_template("register.html")

    username, errors = user.parse_username(request.form["username"])
    password1 = request.form["password1"]
    password2 = request.form["password2"]
    errors += user.validate_password(password1, password2)

    if not errors:
        user_id = user.new_user(username, password1)
        if user_id:
            flash(f"User {username} succesfully created", "success")
            session["user_id"] = user_id
            return redirect("/")
        errors.append("Username is already taken")

    for error in errors:
        flash(error, "error")
    return redirect("/register")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form["username"]
    password = request.form["password"]
    user_id = user.get_user_id(username)

    if not user.check_password(user_id, password):
        flash("Username or password is incorrect.", "error")
        return redirect("/login")

    session["user_id"] = user_id
    return redirect("/")


@app.route("/logout")
@login_required
def logout():
    del session["user_id"]
    return redirect("/")


@app.route("/new", methods=["GET", "POST"])
@login_required
def new_recipe():
    if request.method == "GET":
        return render_template("new.html")

    author_id = session["user_id"]
    title, errors = recipe.parse_title(request.form["title"])
    if errors:
        for error in errors:
            flash(error, "error")
        return redirect("/new")

    recipe_id = recipe.new_recipe(author_id, title)
    return redirect(f"/recipe/{recipe_id}/edit")


@app.route("/recipe/<int:recipe_id>")
def show_recipe(recipe_id):
    r = recipe.get_recipe(recipe_id)
    if r is None:
        abort(404, "This recipe could not be found.")
    is_author = True if r["author_id"] == session["user_id"] else False

    return render_template("recipe.html", recipe=r, is_author=is_author)


@app.route("/recipe/<int:recipe_id>/edit", methods=["GET"])
@login_required
def show_recipe_editpage(recipe_id):
    r = recipe.get_recipe(recipe_id)
    if r is None:
        abort(404, "The recipe you're trying to edit could not be found.")
    if r["author_id"] != session["user_id"]:
        abort(403, "You do not have permission to edit this recipe.")

    return render_template("edit.html", recipe=r)


@app.route("/recipe/<int:recipe_id>/edit", methods=["POST"])
@login_required
def edit_recipe(recipe_id):
    r = recipe.get_recipe(recipe_id)
    if r is None:
        abort(404, "The recipe you're trying to edit could not be found.")
    if r["author_id"] != session["user_id"]:
        abort(403, "You do not have permission to edit this recipe.")

    parts = request.form["action"].split(":")
    action = parts[0]
    item_id = parts[1] if len(parts) == 2 else None
    errors = []

    if action == "rename":
        content, errors = recipe.parse_title(request.form["title"])
        if not errors:
            recipe.update_recipe(recipe_id, content)

    elif action == "tag":
        content, errors = tag.parse_tag(request.form["tag_name"])
        if not errors:
            tag.tag_recipe(recipe_id, content)

    elif action == "add_ingredient":
        content, errors = recipe.parse_ingredient(request.form["ingredient_content"])
        if not errors:
            recipe.new_ingredient(recipe_id, content)

    elif action == "remove_ingredient":
        recipe.delete_ingredient(item_id)

    elif action == "add_instruction":
        content, errors = recipe.parse_ingredient(request.form["instruction_content"])
        if not errors:
            recipe.new_instruction(recipe_id, content)

    elif action == "remove_instruction":
        recipe.delete_instruction(item_id)

    for error in errors:
        flash(error, "error")

    return redirect(f"/recipe/{recipe_id}/edit")


@app.route("/recipe/<int:recipe_id>/delete", methods=["POST"])
@login_required
def delete_recipe(recipe_id):
    r = recipe.get_recipe(recipe_id)
    if r is None:
        abort(404, "The recipe you're trying to edit could not be found.")
    if r["author_id"] != session["user_id"]:
        abort(403, "You do not have permission to edit this recipe.")

    recipe.delete_recipe(recipe_id)
    return redirect("/")


@app.route("/tag/<int:tag_id>")
@app.route("/tag/<tag_name>")
def show_tag(tag_id=None, tag_name=None):
    if tag_name:
        tag_id = tag.get_id(tag_name)

    t = tag.get_tag(tag_id)
    if t is None:
        abort(404, "This tag could not be found.")

    return render_template("tag.html", name=t["name"], recipes=t["recipes"])
