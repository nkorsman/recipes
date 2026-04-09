import database
import recipe


def get_tag(id):
    sql = "SELECT name FROM Tags WHERE id = ?"
    result = database.query_db(sql, [id], one=True)
    if result is None:
        return None

    tag = {"id": id, "name": result[0]}
    tag["recipes"] = recipe.get_recipes(id)

    return tag


def get_id(name):
    sql = "SELECT id FROM Tags WHERE name = ?"
    result = database.query_db(sql, [name], one=True)
    return result[0] if result else None


def parse_tag(input):
    name = input.strip().lower()
    errors = []
    if not name:
        errors.append("Tag must not be blank.")
    if len(name) > 20:
        errors.append("Tag must not be longer than 20 characters.")

    return name, errors


def tag_recipe(recipe_id, tag_name):
    tag_name, errors = parse_tag(tag_name)
    db = database.get_db()
    tag_id = get_id(tag_name)
    if tag_id is None:
        sql = "INSERT INTO Tags (name) VALUES (?)"
        result = db.execute(sql, [tag_name])
        tag_id = result.lastrowid
    else:
        sql = "SELECT id FROM RecipeTags WHERE recipe_id = ? AND tag_id = ?"
        exists = database.query_db(sql, [recipe_id, tag_id], one=True)
        if exists:
            errors.append("Recipe already has this tag.")

    if errors:
        return errors

    sql = "INSERT INTO RecipeTags (recipe_id, tag_id) VALUES (?, ?)"
    db.execute(sql, [recipe_id, tag_id])
    db.commit()


def untag_recipe(recipe_id, tag_id):
    db = database.get_db()

    sql = "DELETE FROM RecipeTags WHERE recipe_id = ? AND tag_id = ?"
    db.execute(sql, [recipe_id, tag_id])

    sql = "SELECT id FROM Tags WHERE id = ?"
    remaining = database.query_db(sql, [tag_id], one=True)
    if not remaining:
        sql = "DELETE FROM Tags WHERE id = ?"
        db.execute(sql, [tag_id])

    db.commit()
