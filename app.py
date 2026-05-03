import math
import secrets
from functools import wraps

import markupsafe
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


@app.template_filter()
def show_lines(content):
    content = str(markupsafe.escape(content))
    content = content.replace("\n", "<br />")
    return markupsafe.Markup(content)


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


def get_recipe_or_404(recipe_id):
    recipe = recipes.get_recipe(recipe_id)
    if recipe is None:
        abort(404, "Recipe could not be found.")
    return recipe


def require_recipe_author(recipe_id):
    if recipes.get_author(recipe_id) != session["user_id"]:
        abort(403, "You do not have permission to edit this recipe.")


def paginate(count_items, get_items, page_size, **kwargs):
    count = count_items(**kwargs)
    page_count = math.ceil(count / page_size)
    page_count = max(page_count, 1)

    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        page = 1
    page = min(max(page, 1), page_count)

    items = get_items(page=page, page_size=page_size, **kwargs)

    return items, page, page_count


@app.errorhandler(404)
@app.errorhandler(403)
@app.errorhandler(401)
def show_error(e):
    return render_template("error.html", error=e)


@app.route("/")
def show_index():
    recipe_list = recipes.get_recipes()
    tag_list = tags.get_tags()
    return render_template("index.html", recipes=recipe_list, tags=tag_list)


@app.route("/recipes")
def show_recipes():
    recipe_list, page, page_count = paginate(
        count_items=recipes.count_recipes, get_items=recipes.get_recipes, page_size=21
    )
    return render_template(
        "paginated_list.html",
        title="All recipes",
        items=recipe_list,
        kind="recipes",
        page=page,
        page_count=page_count,
    )


@app.route("/tags")
def show_tags():
    tag_list, page, page_count = paginate(
        count_items=tags.count_tags, get_items=tags.get_tags, page_size=100
    )
    return render_template(
        "paginated_list.html",
        title="All tags",
        items=tag_list,
        kind="tags",
        page=page,
        page_count=page_count,
    )


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

    return render_template("register.html", filled_username=username)


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
        return render_template("login.html", filled_username=username)

    session["user_id"] = user_id
    session["username"] = username
    session["csrf_token"] = secrets.token_hex(16)
    return redirect("/")


@app.route("/logout", methods=["POST"])
@login_required
@csrf_required
def logout():
    del session["user_id"]
    del session["username"]
    del session["csrf_token"]

    flash("You have been successfully logged out.", "success")
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
    user_id = session.get("user_id")
    recipe = get_recipe_or_404(recipe_id)

    recipe["is_author"] = recipes.get_author(recipe_id) == user_id
    recipe["is_favorite"] = users.is_recipe_favorite(user_id, recipe_id)
    recipe["user_review"] = reviews.get_review(user_id, recipe_id)
    recipe["reviews"] = reviews.get_reviews(recipe_id, excluded_user=user_id)

    if recipe["is_draft"]:
        if recipe["is_author"]:
            flash("You are currently previewing an unpublished recipe.", "info")
        else:
            abort(403, "You do not have permission to view this recipe.")

    return render_template("recipe.html", recipe=recipe)


@app.route("/tag/<tag_name>")
def show_tag(tag_name):
    tag_id = tags.get_id(tag_name)
    if not tag_id:
        abort(404, "This tag could not be found.")

    title = f"All recipes tagged with {tag_name}"
    recipe_list, page, page_count = paginate(
        count_items=recipes.count_recipes,
        get_items=recipes.get_recipes,
        page_size=21,
        tag_id=tag_id,
    )
    return render_template(
        "paginated_list.html",
        title=title,
        items=recipe_list,
        kind="recipes",
        page=page,
        page_count=page_count,
    )


@app.route("/user/<username>")
def show_user(username):
    viewer_id = session.get("user_id")
    user_id = users.get_id(username)
    user = users.get_user(user_id)
    if user is None:
        abort(404, "This user could not be found.")

    user["is_owner"] = user_id == viewer_id

    return render_template("user.html", user=user)


@app.route("/user/<username>/recipes")
def show_user_recipes(username):
    user_id = users.get_id(username)
    if not user_id:
        abort(404, "This user could not be found.")

    title = f"All recipes by {username}"
    recipe_list, page, page_count = paginate(
        count_items=recipes.count_recipes,
        get_items=recipes.get_recipes,
        page_size=21,
        user_id=user_id,
    )
    return render_template(
        "paginated_list.html",
        title=title,
        items=recipe_list,
        kind="recipes",
        page=page,
        page_count=page_count,
    )


@app.route("/user/<username>/favorites")
def show_user_favorites(username):
    user_id = users.get_id(username)
    if not user_id:
        abort(404, "This user could not be found.")

    title = f"Favorite recipes of user {username}"
    recipe_list, page, page_count = paginate(
        count_items=recipes.count_recipes,
        get_items=recipes.get_recipes,
        page_size=21,
        favorited_by=user_id,
    )
    return render_template(
        "paginated_list.html",
        title=title,
        items=recipe_list,
        kind="recipes",
        page=page,
        page_count=page_count,
    )


@app.route("/user/<username>/drafts")
@login_required
def show_user_drafts(username):
    user_id = users.get_id(username)
    if session["user_id"] != user_id:
        abort(403, "You are not authorized to view this page.")

    title = "Your draft recipes"
    recipe_list, page, page_count = paginate(
        count_items=recipes.count_recipes,
        get_items=recipes.get_recipes,
        page_size=21,
        user_id=user_id,
        published=False,
    )
    return render_template(
        "paginated_list.html",
        title=title,
        items=recipe_list,
        kind="recipes",
        page=page,
        page_count=page_count,
    )


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
    recipe = get_recipe_or_404(recipe_id)
    require_recipe_author(recipe_id)

    return render_template("edit/edit.html", recipe=recipe)


@app.route("/recipe/<int:recipe_id>/edit/publish", methods=["POST"])
@login_required
@csrf_required
def publish_recipe(recipe_id):
    get_recipe_or_404(recipe_id)
    require_recipe_author(recipe_id)

    action = request.form["action"]

    if action == "publish":
        recipes.publish_recipe(recipe_id)
    elif action == "unpublish":
        recipes.unpublish_recipe(recipe_id)

    return redirect(f"/recipe/{recipe_id}/edit")


@app.route("/recipe/<int:recipe_id>/edit/<content_type>", methods=["GET", "POST"])
@login_required
@csrf_required
def edit_content(recipe_id, content_type):
    recipe = get_recipe_or_404(recipe_id)
    require_recipe_author(recipe_id)
    if content_type == "ingredients":
        save_items = recipes.save_ingredients
    elif content_type == "instructions":
        save_items = recipes.save_instructions
    else:
        return abort(404)

    if request.method == "GET":
        items = [i["content"] for i in recipe[content_type]]
        if not items:
            items = [""]
        return render_template(f"edit/{content_type}.html", recipe=recipe, items=items)

    parts = request.form["action"].split(":")
    action = parts[0]
    items = request.form.getlist("item")

    if action == "cancel":
        return redirect(f"/recipe/{recipe_id}/edit")
    if action == "new":
        items.append("")
    elif action == "remove":
        index = int(parts[1])
        items.pop(index)
    elif action == "save":
        errors = save_items(recipe_id, items)
        if errors:
            for error in errors:
                flash(error, "error")
        else:
            return redirect(f"/recipe/{recipe_id}/edit")

    return render_template(f"edit/{content_type}.html", recipe=recipe, items=items)


@app.route("/recipe/<int:recipe_id>/edit/rename", methods=["GET", "POST"])
@login_required
@csrf_required
def rename_recipe(recipe_id):
    recipe = get_recipe_or_404(recipe_id)
    require_recipe_author(recipe_id)

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
def edit_tags(recipe_id):
    recipe = get_recipe_or_404(recipe_id)
    require_recipe_author(recipe_id)

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
def delete_recipe(recipe_id):
    require_recipe_author(recipe_id)
    recipes.delete_recipe(recipe_id)
    return redirect("/")


@app.route("/recipe/<int:recipe_id>/review", methods=["GET", "POST"])
@login_required
@csrf_required
def review_recipe(recipe_id):
    recipe = get_recipe_or_404(recipe_id)
    if request.method == "GET":
        review = reviews.get_review(session["user_id"], recipe_id)
        return render_template("review.html", recipe=recipe, review=review)

    user_id = session["user_id"]
    rating = request.form["rating"]
    comment = request.form["comment"]
    action = request.form["action"]

    if action == "submit":
        error = reviews.leave_review(recipe_id, user_id, rating, comment)
        if error:
            flash(error, "error")
    elif action == "remove":
        reviews.remove_review(recipe_id, user_id)

    return redirect(f"/recipe/{recipe_id}")


@app.route("/recipe/<int:recipe_id>/reviews")
def show_reviews(recipe_id):
    recipe = get_recipe_or_404(recipe_id)
    title = f"All reviews of {recipe['title']}"
    review_list, page, page_count = paginate(
        count_items=reviews.count_reviews,
        get_items=reviews.get_reviews,
        page_size=5,
        recipe_id=recipe_id,
    )

    return render_template(
        "paginated_list.html",
        title=title,
        items=review_list,
        kind="reviews",
        page=page,
        page_count=page_count,
    )


@app.route("/user/<username>/reviews")
def show_user_reviews(username):
    user_id = users.get_id(username)
    if not user_id:
        abort(404, "This user could not be found.")

    title = f"All reviews by {username}"
    review_list, page, page_count = paginate(
        count_items=reviews.count_user_reviews,
        get_items=reviews.get_user_reviews,
        page_size=5,
        user_id=user_id,
    )
    return render_template(
        "paginated_list.html",
        title=title,
        items=review_list,
        kind="reviews",
        page=page,
        page_count=page_count,
    )
