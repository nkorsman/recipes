import database


def get_recipes(tag_id=None, user_id=None, favorited_by=None):
    sql = """SELECT R.id, R.title, U.username
             FROM Recipes R
             JOIN Users U ON U.id = R.author_id"""

    joins = []
    conditions = []
    parameters = []

    if tag_id:
        joins.append("JOIN RecipeTags T ON T.recipe_id = R.id")
        conditions.append("T.tag_id = ?")
        parameters.append(tag_id)
    if user_id:
        conditions.append("R.author_id = ?")
        parameters.append(user_id)
    if favorited_by:
        joins.append("JOIN UserFavorites F ON F.recipe_id = R.id")
        conditions.append("F.user_id = ?")
        parameters.append(favorited_by)

    if joins:
        sql += "\n" + "\n".join(joins)
    if conditions:
        sql += "\nWHERE " + " AND ".join(conditions)

    return database.query_db(sql, parameters)


def get_recipe(recipe_id, viewer_id=None):
    sql = """SELECT id, title, created_at, updated_at, author_id
             FROM Recipes
             WHERE id = ?"""
    result = database.query_db(sql, [recipe_id], one=True)
    if result is None:
        return None

    recipe = dict(result)
    recipe["is_author"] = viewer_id == recipe["author_id"]

    sql = "SELECT id FROM UserFavorites WHERE recipe_id = ? AND user_id = ?"
    result = database.query_db(sql, [recipe_id, viewer_id], one=True)
    recipe["is_favorite"] = result is not None

    sql = """SELECT id, content, ingredient_number
             FROM RecipeIngredients
             WHERE recipe_id = ?
             ORDER BY ingredient_number"""
    recipe["ingredients"] = database.query_db(sql, [recipe_id])

    sql = """SELECT id, content, instruction_number
             FROM RecipeInstructions
             WHERE recipe_id = ?
             ORDER BY instruction_number"""
    recipe["instructions"] = database.query_db(sql, [recipe_id])

    sql = "SELECT T.id, T.name FROM Tags T, RecipeTags R WHERE R.recipe_id = ? AND T.id = R.tag_id"
    recipe["tags"] = database.query_db(sql, [recipe_id])

    return recipe


def get_author(recipe_id):
    sql = "SELECT author_id FROM Recipes WHERE id = ?"
    result = database.query_db(sql, [recipe_id], one=True)
    return result[0] if result else None


def search_recipes(query):
    query = f"%{query}%"
    sql = """SELECT DISTINCT R.id, R.title, U.username
             FROM Recipes R
             JOIN Users U ON U.id = R.author_id
             JOIN RecipeIngredients G ON G.recipe_id = R.id
             JOIN RecipeInstructions S ON S.recipe_id = R.id
             WHERE R.title LIKE ?
             OR G.content LIKE ?
             OR S.content LIKE ?"""
    return database.query_db(sql, [query, query, query])


def parse_title(input):
    title = input.strip()
    errors = []

    if not title:
        errors.append("Title must not be blank.")
    if len(title) > 50:
        errors.append("Title must not be longer than 50 characters")

    return title, errors


def new_recipe(author_id, title):
    title, errors = parse_title(title)
    if errors:
        return None, errors

    db = database.get_db()
    sql = "INSERT INTO Recipes (title, author_id, created_at, updated_at) VALUES (?, ?, DATETIME('now'), DATETIME('now'))"
    result = db.execute(sql, [title, author_id])
    db.commit()
    return result.lastrowid, None


def rename_recipe(recipe_id, title):
    title, errors = parse_title(title)
    if errors:
        return errors

    db = database.get_db()
    sql = "UPDATE Recipes SET title = ?, updated_at = DATETIME('now') WHERE id = ?"
    db.execute(sql, [title, recipe_id])
    db.commit()


def delete_recipe(id):
    db = database.get_db()
    sql = "DELETE FROM Recipes WHERE id = ?"
    db.execute(sql, [id])
    db.commit()


def parse_ingredient(input):
    ingredient = input.strip()
    errors = []

    if not ingredient:
        errors.append("Ingredient must not be empty.")
    if len(ingredient) > 100:
        errors.append("Ingredient must not be longer than 100 characters.")

    return ingredient, errors


def parse_instruction(input):
    instruction = input.strip()
    errors = []

    if not instruction:
        errors.append("Instruction must not be empty.")
    if len(instruction) > 1000:
        errors.append("Instruction must not be longer than 1000 characters.")

    return instruction, errors


def save_ingredients(recipe_id, ingredients):
    errors = []
    db = database.get_db()
    sql = "DELETE FROM RecipeIngredients WHERE recipe_id = ?"
    db.execute(sql, [recipe_id])

    for i, ingredient in enumerate(ingredients):
        ingredient, e = parse_ingredient(ingredient)
        for msg in e:
            errors.append(f"Ingredient {i + 1}: {msg}")
        sql = """INSERT INTO RecipeIngredients
                 (content, ingredient_number, recipe_id)
                 VALUES (?, ?, ?)"""
        db.execute(sql, [ingredient, i, recipe_id])

    sql = "UPDATE Recipes SET updated_at = DATETIME('now') WHERE id = ?"
    db.execute(sql, [recipe_id])

    if not errors:
        db.commit()

    return errors


def save_instructions(recipe_id, instructions):
    errors = []
    db = database.get_db()
    sql = "DELETE FROM RecipeInstructions WHERE recipe_id = ?"
    db.execute(sql, [recipe_id])

    for i, instruction in enumerate(instructions):
        instruction, e = parse_instruction(instruction)
        for msg in e:
            errors.append(f"Step {i + 1}: {msg}")
        sql = """INSERT INTO RecipeInstructions
                 (content, instruction_number, recipe_id)
                 VALUES (?, ?, ?)"""
        db.execute(sql, [instruction, i, recipe_id])

    sql = "UPDATE Recipes SET updated_at = DATETIME('now') WHERE id = ?"
    db.execute(sql, [recipe_id])

    if not errors:
        db.commit()

    return errors


def favorite_recipe(recipe_id, user_id):
    db = database.get_db()
    sql = "INSERT INTO UserFavorites (recipe_id, user_id) VALUES (?, ?)"
    db.execute(sql, [recipe_id, user_id])
    db.commit()


def unfavorite_recipe(recipe_id, user_id):
    db = database.get_db()
    sql = "DELETE FROM UserFavorites WHERE recipe_id = ? AND user_id = ?"
    db.execute(sql, [recipe_id, user_id])
    db.commit()
