import database
import recipes


def get_reviews(recipe_id, page=1, page_size=4, excluded_user=None):
    parameters = [recipe_id]
    condition = ""
    if excluded_user:
        condition = "AND U.id != ?"
        parameters.append(excluded_user)

    parameters.append(page_size)
    parameters.append(page_size * (page - 1))

    sql = f"""SELECT U.username, R.rating, R.content, R.updated_at
             FROM Reviews R
             JOIN Users U on U.id = R.user_id
             WHERE R.recipe_id = ?
             {condition}
             ORDER BY R.updated_at DESC
             LIMIT ? OFFSET ?"""
    return database.query_db(sql, parameters)


def get_user_reviews(user_id, page=1, page_size=3):
    limit = page_size
    offset = page_size * (page - 1)
    sql = """SELECT C.id, C.title, R.rating, R.content, R.updated_at
             FROM Reviews R
             JOIN Recipes C on C.id = R.recipe_id
             WHERE R.user_id = ?
             ORDER BY R.updated_at DESC
             LIMIT ? OFFSET ?"""
    return database.query_db(sql, [user_id, limit, offset])


def count_reviews(recipe_id, excluded_user=None):
    parameters = [recipe_id]
    condition = ""
    if excluded_user:
        condition = "AND U.id != ?"
        parameters.append(excluded_user)

    sql = f"""SELECT COUNT(*)
             FROM Reviews R
             JOIN Users U ON U.id = R.user_id
             WHERE R.recipe_id = ?
             {condition}
             """
    result = database.query_db(sql, parameters, one=True)
    return result[0] if result else 0


def count_user_reviews(user_id):
    sql = "SELECT COUNT(*) FROM Reviews R WHERE R.user_id = ?"
    result = database.query_db(sql, [user_id], one=True)
    return result[0] if result else 0


def user_has_reviewed(user_id, recipe_id):
    sql = "SELECT id FROM Reviews WHERE user_id = ? AND recipe_id = ?"
    exists = database.query_db(sql, [user_id, recipe_id], one=True)
    return exists is not None


def get_review(user_id, recipe_id):
    sql = """SELECT U.username, R.rating, R.content, R.updated_at, R.recipe_id
             FROM Reviews R
             JOIN Users U on U.id = R.user_id
             WHERE R.recipe_id = ?
             AND R.user_id = ?"""
    return database.query_db(sql, [recipe_id, user_id], one=True)


def leave_review(recipe_id, user_id, rating, comment):
    rating = int(rating) if rating else None
    if len(comment) > 500:
        return "Review cannot be longer than 500 characters."
    if not comment:
        comment = None

    db = database.get_db()
    if user_id == recipes.get_author(recipe_id):
        return "You may not review your own recipe."

    sql = "SELECT id FROM Reviews WHERE user_id = ? AND recipe_id = ?"
    result = database.query_db(sql, [user_id, recipe_id], one=True)
    if result:
        sql = """UPDATE Reviews SET rating = ?, content = ?, updated_at = DATETIME('now')
                 WHERE id = ?"""
        db.execute(sql, [rating, comment, result[0]])
    else:
        sql = """INSERT INTO Reviews (recipe_id, user_id, rating, content, created_at, updated_at)
                 VALUES (?, ?, ?, ?, DATETIME('now'), DATETIME('now'))"""
        db.execute(sql, [recipe_id, user_id, rating, comment])

    db.commit()
    return None


def remove_review(recipe_id, user_id):
    db = database.get_db()
    sql = "DELETE FROM Reviews WHERE recipe_id = ? AND user_id = ?"
    db.execute(sql, [recipe_id, user_id])
    db.commit()
