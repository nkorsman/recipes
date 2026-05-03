import database


def get_tags(page=1, page_size=30):
    limit = page_size
    offset = page_size * (page - 1)
    sql = """SELECT T.name, T.recipe_count
             FROM Tags T
             ORDER BY recipe_count DESC
             LIMIT ? OFFSET ?"""
    return database.query_db(sql, [limit, offset])


def count_tags():
    sql = "SELECT COUNT(*) FROM Tags"
    result = database.query_db(sql, one=True)
    return result[0] if result else 0


def get_id(name):
    sql = "SELECT id FROM Tags WHERE name = ?"
    result = database.query_db(sql, [name], one=True)
    return result[0] if result else None


def parse_tag(user_input):
    name = user_input.strip().lower()
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
        sql = "INSERT INTO Tags (name, recipe_count) VALUES (?, 0)"
        result = db.execute(sql, [tag_name])
        tag_id = result.lastrowid
    else:
        sql = "SELECT id FROM RecipeTags WHERE recipe_id = ? AND tag_id = ?"
        exists = database.query_db(sql, [recipe_id, tag_id], one=True)
        if exists:
            errors.append("Recipe already has this tag.")

    sql = "SELECT COUNT(*) FROM RecipeTags WHERE recipe_id = ?"
    result = database.query_db(sql, [recipe_id], one=True)
    if result:
        if result[0] >= 10:
            return "Recipe cannot have more than 10 tags."

    if errors:
        return errors

    sql = "INSERT INTO RecipeTags (recipe_id, tag_id) VALUES (?, ?)"
    db.execute(sql, [recipe_id, tag_id])
    sql = "UPDATE Tags SET recipe_count = recipe_count + 1 WHERE id = ?"
    db.execute(sql, [tag_id])
    db.commit()
    return []


def untag_recipe(recipe_id, tag_id):
    db = database.get_db()

    sql = "DELETE FROM RecipeTags WHERE recipe_id = ? AND tag_id = ?"
    db.execute(sql, [recipe_id, tag_id])

    sql = "SELECT recipe_count FROM Tags WHERE id = ?"
    result = database.query_db(sql, [tag_id], one=True)
    if result[0] >= 1:
        sql = "UPDATE Tags SET recipe_count = recipe_count - 1 WHERE id = ?"
        db.execute(sql, [tag_id])
    else:
        sql = "DELETE FROM Tags WHERE id = ?"

    db.commit()
