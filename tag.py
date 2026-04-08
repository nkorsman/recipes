import database


def get_tag(id):
    sql = "SELECT id, name FROM Tags WHERE id = ?"
    return database.query_db(sql, [id], one=True)


def get_id(name):
    sql = "SELECT id FROM Tags WHERE name = ?"
    result = database.query_db(sql, [name], one=True)
    return result[0] if result else None


def tag_recipe(recipe_id, tag_name):
    db = database.get_db()
    tag_id = get_id(tag_name)
    if tag_id is None:
        sql = "INSERT INTO Tags (name) VALUES (?)"
        result = db.execute(sql, [tag_name])
        tag_id = result.lastrowid

    sql = "INSERT INTO RecipeTags (recipe_id, tag_id) VALUES (?, ?)"
    db.execute(sql, [recipe_id, tag_id])
    db.commit()
