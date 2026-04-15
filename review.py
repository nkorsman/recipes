import database


def leave_review(recipe_id, user_id, rating=None, comment=None):
    db = database.get_db()
    sql = """INSERT INTO Reviews (recipe_id, user_id, rating, content, created_at, updated_at)
             VALUES (?, ?, ?, ?, DATETIME('now'), DATETIME('now'))"""
    db.execute(sql, [recipe_id, user_id, rating, comment])
    db.commit()
