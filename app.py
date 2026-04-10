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


def recipe_owner_required(f):
    @wraps(f)
    def decorated_function(recipe_id, *args, **kwargs):
        author_id = recipe.get_author(recipe_id)
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
    recipes = recipe.get_recipes()
    return render_template("index.html", recipes=recipes)


@app.route("/search")
def search():
    query = request.args.get("q")
    results = recipe.search_recipes(query) if query else None
    return render_template("search.html", query=query, recipes=results)


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
            session["username"] = username
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
    user_id = user.get_id(username)

    if not user.check_password(user_id, password):
        flash("Username or password is incorrect.", "error")
        return redirect("/login")

    session["user_id"] = user_id
    session["username"] = username
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
    title = request.form["title"]

    recipe_id, errors = recipe.new_recipe(author_id, title)
    if errors:
        for error in errors:
            flash(error, "error")
        return redirect("/new")

    return redirect(f"/recipe/{recipe_id}/edit")


@app.route("/recipe/<int:recipe_id>")
def show_recipe(recipe_id):
    r = recipe.get_recipe(recipe_id)
    if r is None:
        abort(404, "This recipe could not be found.")

    if "user_id" in session:
        is_author = session["user_id"] == r["author_id"]
    else:
        is_author = False

    return render_template("recipe.html", recipe=r, is_author=is_author)


@app.route("/tag/<tag_name>")
def show_tag(tag_name):
    tag_id = tag.get_id(tag_name)
    t = tag.get_tag(tag_id)
    if t is None:
        abort(404, "This tag could not be found.")

    return render_template("tag.html", name=t["name"], recipes=t["recipes"])


@app.route("/user/<username>")
def show_user(username):
    user_id = user.get_id(username)
    u = user.get_user(user_id)
    if u is None:
        abort(404, "This user could not be found.")

    return render_template("user.html", name=u["name"], recipes=u["recipes"])


@app.route("/recipe/<int:recipe_id>/edit", methods=["GET"])
@login_required
@recipe_owner_required
def edit_recipe(recipe_id):
    r = recipe.get_recipe(recipe_id)
    return render_template("edit/edit.html", recipe=r)


@app.route("/recipe/<int:recipe_id>/edit/ingredients", methods=["GET", "POST"])
@login_required
@recipe_owner_required
def edit_ingredients(recipe_id):
    r = recipe.get_recipe(recipe_id)
    if r is None:
        abort(404, "Recipe could not be found.")

    if request.method == "GET":
        if r["ingredients"]:
            ingredients = [i["content"] for i in r["ingredients"]]
        else:
            ingredients = [""]
        return render_template(
            "edit/ingredients.html", recipe=r, ingredients=ingredients
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
        errors = recipe.save_ingredients(recipe_id, ingredients)
        if errors:
            for error in errors:
                flash(error, "error")
        else:
            return redirect(f"/recipe/{recipe_id}/edit")

    return render_template("edit/ingredients.html", recipe=r, ingredients=ingredients)


@app.route("/recipe/<int:recipe_id>/edit/instructions", methods=["GET", "POST"])
@login_required
@recipe_owner_required
def edit_instructions(recipe_id):
    r = recipe.get_recipe(recipe_id)
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
        errors = recipe.save_instructions(recipe_id, instructions)
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
@recipe_owner_required
def rename_recipe(recipe_id):
    r = recipe.get_recipe(recipe_id)
    if r is None:
        abort(404, "Recipe could not be found.")
    if request.method == "GET":
        title = r["title"]
        return render_template("edit/rename.html", recipe=r, title=title)

    action = request.form["action"]
    title = request.form["title"]

    if action == "save":
        errors = recipe.rename_recipe(recipe_id, title)
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("edit/rename.html", recipe=r, title=title)

    return redirect(f"/recipe/{recipe_id}/edit")


@app.route("/recipe/<int:recipe_id>/edit/tags", methods=["GET", "POST"])
@login_required
@recipe_owner_required
def edit_tags(recipe_id):
    r = recipe.get_recipe(recipe_id)
    if r is None:
        abort(404, "Recipe could not be found.")

    if request.method == "GET":
        return render_template("edit/tags.html", recipe=r)

    parts = request.form["action"].split(":")
    action = parts[0]

    if action == "done":
        return redirect(f"/recipe/{recipe_id}/edit")
    elif action == "new":
        tag.tag_recipe(recipe_id, request.form["new_tag"])
    elif action == "remove":
        tag_id = r["tags"][int(parts[1])]["id"]
        tag.untag_recipe(recipe_id, tag_id)

    return redirect(f"/recipe/{recipe_id}/edit/tags")


@app.route("/recipe/<int:recipe_id>/edit/delete", methods=["POST"])
@login_required
@recipe_owner_required
def delete_recipe(recipe_id):
    recipe.delete_recipe(recipe_id)
    return redirect("/")
