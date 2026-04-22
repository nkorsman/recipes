import database
import users


def user_has_reviewed(user_id, recipe_id):
    sql = "SELECT id FROM Reviews WHERE user_id = ? AND recipe_id = ?"
    exists = database.query_db(sql, [user_id, recipe_id], one=True)
    return exists is not None


def get_user_review(user_id, recipe_id):
    sql = """SELECT R.rating, R.content
             FROM Reviews R
             WHERE R.recipe_id = ?
             AND R.user_id = ?"""
    return database.query_db(sql, [recipe_id, user_id], one=True)


def leave_review(recipe_id, user_id, rating, comment):
    rating = int(rating) if rating else None
    if not comment:
        comment = None

    db = database.get_db()
    if users.is_recipe_author(user_id, recipe_id):
        return "You may not review your own recipe."

    sql = "SELECT id FROM Reviews WHERE user_id = ? AND recipe_id = ?"
    id = database.query_db(sql, [user_id, recipe_id], one=True)
    if id:
        sql = "UPDATE Reviews SET rating = ?, content = ?, updated_at = DATETIME('now') WHERE id = ?"
        db.execute(sql, [rating, comment, id[0]])
    else:
        sql = """INSERT INTO Reviews (recipe_id, user_id, rating, content, created_at, updated_at)
                VALUES (?, ?, ?, ?, DATETIME('now'), DATETIME('now'))"""
        db.execute(sql, [recipe_id, user_id, rating, comment])

    db.commit()
    return None
