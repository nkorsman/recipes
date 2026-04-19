import secrets
from functools import wraps

from flask import Flask, abort, flash, redirect, render_template, request, session

import config
import database
import recipes
import reviews
import tags
import users

app = Flask(__name__)
app.teardown_appcontext(database.close_db)
app.secret_key = config.secret_key


def csrf_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == "POST":
            if "csrf_token" not in request.form:
                abort(401, "CSRF token missing")
            elif request.form["csrf_token"] != session["csrf_token"]:
                abort(403, "Invalid CSRF token.")
        return f(*args, **kwargs)

    return decorated_function


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            abort(401, "You must be logged in to perform this action.")
        return f(*args, **kwargs)

    return decorated_function


def recipe_owner_required(f):
    @wraps(f)
    def decorated_function(recipe_id, *args, **kwargs):
        author_id = recipes.get_author(recipe_id)
        if author_id is None:
            abort(404, "Recipe could not be found.")
        if author_id != session["user_id"]:
            abort(403, "You do not have permission to edit this recipe.")
        return f(recipe_id, *args, **kwargs)

    return decorated_function


@app.errorhandler(404)
@app.errorhandler(403)
@app.errorhandler(401)
def error(e):
    return render_template("error.html", error=e)


@app.route("/")
def index():
    recipe_list = recipes.get_recipes()
    tag_list = tags.get_tags()
    return render_template("index.html", recipes=recipe_list, tags=tag_list)


@app.route("/search")
def search():
    query = request.args.get("q")
    results = recipes.search_recipes(query) if query else None
    return render_template("search.html", query=query, recipes=results)


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        abort(403, "You must log out first before you can register a new account.")
    if request.method == "GET":
        return render_template("register.html")

    username, errors = users.parse_username(request.form["username"])
    password1 = request.form["password1"]
    password2 = request.form["password2"]
    errors += users.validate_password(password1, password2)

    if not errors:
        user_id = users.new_user(username, password1)
        if user_id:
            flash(f"User {username} successfully created", "success")
            session["user_id"] = user_id
            session["username"] = username
            session["csrf_token"] = secrets.token_hex(16)
            return redirect("/")
        errors.append("Username is already taken")

    for error in errors:
        flash(error, "error")
    return redirect("/register")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        abort(403, "You must log out first before you can log in.")
    if request.method == "GET":
        return render_template("login.html")

    username = request.form["username"]
    password = request.form["password"]
    user_id = users.get_id(username)

    if not users.check_password(user_id, password):
        flash("Username or password is incorrect.", "error")
        return redirect("/login")

    session["user_id"] = user_id
    session["username"] = username
    session["csrf_token"] = secrets.token_hex(16)
    return redirect("/")


@app.route("/logout")
@login_required
def logout():
    del session["user_id"]
    del session["username"]
    del session["csrf_token"]
    return redirect("/")


@app.route("/new", methods=["GET", "POST"])
@login_required
@csrf_required
def new_recipe():
    if request.method == "GET":
        return render_template("new.html")

    author_id = session["user_id"]
    title = request.form["title"]

    recipe_id, errors = recipes.new_recipe(author_id, title)
    if errors:
        for error in errors:
            flash(error, "error")
        return redirect("/new")

    return redirect(f"/recipe/{recipe_id}/edit")


@app.route("/recipe/<int:recipe_id>")
def show_recipe(recipe_id):
    user_id = session["user_id"] if "user_id" in session else None
    recipe = recipes.get_recipe(recipe_id)
    if recipe is None:
        abort(404, "This recipe could not be found.")

    recipe["is_author"] = users.is_recipe_author(user_id, recipe_id)
    recipe["is_favorite"] = users.is_recipe_favorite(user_id, recipe_id)

    if recipe["is_draft"]:
        if recipe["is_author"]:
            flash("You are currently previewing an unpublished recipe.", "info")
        else:
            abort(403, "You do not have permission to view this recipe.")

    return render_template("recipe.html", recipe=recipe)


@app.route("/tag/<tag_name>")
def show_tag(tag_name):
    tag_id = tags.get_id(tag_name)
    tag = tags.get_tag(tag_id)
    if tag is None:
        abort(404, "This tag could not be found.")

    return render_template("tag.html", tag=tag)


@app.route("/user/<username>")
def show_user(username):
    viewer_id = session["user_id"] if "user_id" in session else None
    user_id = users.get_id(username)
    user = users.get_user(user_id)
    if user is None:
        abort(404, "This user could not be found.")

    user["is_owner"] = user_id == viewer_id

    return render_template("user.html", user=user)


@app.route("/recipe/<int:recipe_id>/favorite", methods=["POST"])
@login_required
@csrf_required
def favorite_recipe(recipe_id):
    user_id = session["user_id"]
    action = request.form["action"]

    if action == "favorite":
        recipes.favorite_recipe(recipe_id, user_id)
    elif action == "unfavorite":
        recipes.unfavorite_recipe(recipe_id, user_id)

    return redirect(f"/recipe/{recipe_id}")


@app.route("/recipe/<int:recipe_id>/edit", methods=["GET"])
@login_required
def edit_recipe(recipe_id):
    recipe = recipes.get_recipe(recipe_id)
    if recipe is None:
        abort(404, "This recipe could not be found.")
    if not users.is_recipe_author(session["user_id"], recipe_id):
        abort(403, "You do not have permission to edit this recipe.")

    return render_template("edit/edit.html", recipe=recipe)


@app.route("/recipe/<int:recipe_id>/edit/publish", methods=["POST"])
@login_required
@csrf_required
@recipe_owner_required
def publish_recipe(recipe_id):
    recipe = recipes.get_recipe(recipe_id)
    if recipe is None:
        abort(404, "This recipe could not be found.")
    if not users.is_recipe_author(session["user_id"], recipe_id):
        abort(403, "You do not have permission to edit this recipe.")

    action = request.form["action"]

    if action == "publish":
        recipes.publish_recipe(recipe_id)
    elif action == "unpublish":
        recipes.unpublish_recipe(recipe_id)

    return redirect(f"/recipe/{recipe_id}/edit")


@app.route("/recipe/<int:recipe_id>/edit/ingredients", methods=["GET", "POST"])
@login_required
@csrf_required
@recipe_owner_required
def edit_ingredients(recipe_id):
    recipe = recipes.get_recipe(recipe_id)
    if recipe is None:
        abort(404, "Recipe could not be found.")

    if request.method == "GET":
        if recipe["ingredients"]:
            ingredients = [i["content"] for i in recipe["ingredients"]]
        else:
            ingredients = [""]
        return render_template(
            "edit/ingredients.html", recipe=recipe, ingredients=ingredients
        )

    parts = request.form["action"].split(":")
    action = parts[0]
    ingredients = request.form.getlist("ingredient")

    if action == "cancel":
        return redirect(f"/recipe/{recipe_id}/edit")
    elif action == "new":
        ingredients.append("")
    elif action == "remove":
        ingredients.pop(int(parts[1]))
    elif action == "save":
        errors = recipes.save_ingredients(recipe_id, ingredients)
        if errors:
            for error in errors:
                flash(error, "error")
        else:
            return redirect(f"/recipe/{recipe_id}/edit")

    return render_template(
        "edit/ingredients.html", recipe=recipe, ingredients=ingredients
    )


@app.route("/recipe/<int:recipe_id>/edit/instructions", methods=["GET", "POST"])
@login_required
@csrf_required
@recipe_owner_required
def edit_instructions(recipe_id):
    r = recipes.get_recipe(recipe_id)
    if r is None:
        abort(404, "Recipe could not be found.")

    if request.method == "GET":
        if r["instructions"]:
            instructions = [i["content"] for i in r["instructions"]]
        else:
            instructions = [""]
        return render_template(
            "edit/instructions.html", recipe=r, instructions=instructions
        )

    parts = request.form["action"].split(":")
    action = parts[0]
    instructions = request.form.getlist("instruction")

    if action == "cancel":
        return redirect(f"/recipe/{recipe_id}/edit")
    elif action == "new":
        instructions.append("")
    elif action == "remove":
        instructions.pop(int(parts[1]))
    elif action == "save":
        errors = recipes.save_instructions(recipe_id, instructions)
        if errors:
            for error in errors:
                flash(error, "error")
        else:
            return redirect(f"/recipe/{recipe_id}/edit")

    return render_template(
        "edit/instructions.html", recipe=r, instructions=instructions
    )


@app.route("/recipe/<int:recipe_id>/edit/rename", methods=["GET", "POST"])
@login_required
@csrf_required
@recipe_owner_required
def rename_recipe(recipe_id):
    recipe = recipes.get_recipe(recipe_id)
    if recipe is None:
        abort(404, "Recipe could not be found.")
    if request.method == "GET":
        title = recipe["title"]
        return render_template("edit/rename.html", recipe=recipe, title=title)

    action = request.form["action"]
    title = request.form["title"]

    if action == "save":
        errors = recipes.rename_recipe(recipe_id, title)
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("edit/rename.html", recipe=recipe, title=title)

    return redirect(f"/recipe/{recipe_id}/edit")


@app.route("/recipe/<int:recipe_id>/edit/tags", methods=["POST"])
@login_required
@csrf_required
@recipe_owner_required
def edit_tags(recipe_id):
    recipe = recipes.get_recipe(recipe_id)
    if recipe is None:
        abort(404, "Recipe could not be found.")

    parts = request.form["action"].split(":")
    action = parts[0]

    if action == "new":
        errors = tags.tag_recipe(recipe_id, request.form["new_tag"])
        for error in errors:
            flash(error, "error")
    elif action == "remove":
        tag_id = recipe["tags"][int(parts[1])]["id"]
        tags.untag_recipe(recipe_id, tag_id)

    return redirect(f"/recipe/{recipe_id}/edit")


@app.route("/recipe/<int:recipe_id>/edit/delete", methods=["POST"])
@login_required
@csrf_required
@recipe_owner_required
def delete_recipe(recipe_id):
    recipes.delete_recipe(recipe_id)
    return redirect("/")


@app.route("/recipe/<int:recipe_id>/reviews/add", methods=["POST"])
@login_required
@csrf_required
def review_recipe(recipe_id):
    user_id = session["user_id"]
    if request.form["rating"]:
        rating = int(request.form["rating"])
    else:
        rating = None

    if request.form["comment"]:
        comment = request.form["comment"]
    else:
        comment = None

    error = reviews.leave_review(recipe_id, user_id, rating, comment)
    if error:
        flash(error, "error")
    return redirect(f"/recipe/{recipe_id}")
