import database


def get_recipes():
    sql = """SELECT R.id, R.title, U.username
             FROM Recipes R, Users U
             WHERE R.author_id = U.id"""
    return database.query_db(sql)


def get_recipe(id):
    sql = "SELECT id, title FROM Recipes WHERE id = ?"
    return database.query_db(sql, [id], one=True)


def new_recipe(author_id, title):
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


def delete_recipe(id):
    db = database.get_db()

    sql = "DELETE FROM RecipeIngredients WHERE recipe_id = ?"
    db.execute(sql, [id])

    sql = "DELETE FROM RecipeInstructions WHERE recipe_id = ?"
    db.execute(sql, [id])

    sql = "DELETE FROM Recipes WHERE id = ?"
    db.execute(sql, [id])

    db.commit()


def get_ingredients(recipe_id):
    sql = """SELECT id, content, ingredient_number
             FROM RecipeIngredients
             WHERE recipe_id = ?
             ORDER BY ingredient_number"""
    return database.query_db(sql, [recipe_id])


def next_ingredient_number(recipe_id):
    sql = "SELECT MAX(ingredient_number) FROM RecipeIngredients WHERE recipe_id = ?"
    result = database.query_db(sql, [recipe_id], one=True)
    if result is None or result[0] is None:
        return 1

    return result[0] + 1


def new_ingredient(recipe_id, number, content):
    db = database.get_db()
    sql = """INSERT INTO RecipeIngredients
             (content, ingredient_number, recipe_id)
             VALUES (?, ?, ?)"""
    db.execute(sql, [content, number, recipe_id])
    db.commit()


def delete_ingredient(id):
    db = database.get_db()
    sql = "DELETE FROM RecipeIngredients WHERE id = ?"
    db.execute(sql, [id])
    db.commit()


def get_instructions(recipe_id):
    sql = """SELECT id, content, instruction_number
             FROM RecipeInstructions
             WHERE recipe_id = ?
             ORDER BY instruction_number"""
    return database.query_db(sql, [recipe_id])


def next_instruction_number(recipe_id):
    sql = "SELECT MAX(instruction_number) FROM RecipeInstructions WHERE recipe_id = ?"
    result = database.query_db(sql, [recipe_id], one=True)
    if result is None or result[0] is None:
        return 1

    return result[0] + 1


def new_instruction(recipe_id, number, content):
    db = database.get_db()
    sql = """INSERT INTO RecipeInstructions
            (content, instruction_number, recipe_id)
            VALUES (?, ?, ?)"""
    db.execute(sql, [content, number, recipe_id])
    db.commit()


def delete_instruction(id):
    db = database.get_db()
    sql = "DELETE FROM RecipeInstructions WHERE id = ?"
    db.execute(sql, [id])
    db.commit()
