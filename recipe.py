import database


def get_recipes():
    sql = """SELECT R.id, R.title, U.username
             FROM Recipes R, Users U
             WHERE R.author_id = U.id
    """
    return database.query_db(sql)


def get_recipe(id):
    sql = "SELECT title FROM Recipes WHERE id = ?"
    return database.query_db(sql, [id], one=True)


def new_recipe(author_id):
    title = "Untitled recipe"

    db = database.get_db()
    sql = "INSERT INTO Recipes (title, author_id) VALUES (?, ?)"
    result = db.execute(sql, [title, author_id])
    db.commit()
    return result.lastrowid


def update_recipe(id, title):
    db = database.get_db()
    sql = "UPDATE Recipes SET title = ? WHERE id = ?"
    db.execute(sql, [title, id])
    db.commit()
    return get_recipe(id)
