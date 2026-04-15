import database
import user


def leave_review(recipe_id, user_id, rating=None, comment=None):
    if user.is_recipe_author(user_id, recipe_id):
        return "You may not review your own recipe."

    db = database.get_db()
    sql = """INSERT INTO Reviews (recipe_id, user_id, rating, content, created_at, updated_at)
             VALUES (?, ?, ?, ?, DATETIME('now'), DATETIME('now'))"""
    db.execute(sql, [recipe_id, user_id, rating, comment])
    db.commit()
    return None
