import database


def get_recipes(tag=None):
    sql = """SELECT R.id, R.title, U.username
             FROM Recipes R
             JOIN Users U ON U.id = R.author_id"""
    if tag:
        sql += """\nJOIN RecipeTags T ON T.recipe_id = R.id
                    WHERE T.tag_id = ?"""
        return database.query_db(sql, [tag])

    return database.query_db(sql)


def get_recipe(recipe_id):
    sql = "SELECT title, author_id FROM Recipes WHERE id = ?"
    result = database.query_db(sql, [recipe_id], one=True)
    if result is None:
        return None

    recipe = {"id": recipe_id, "title": result[0], "author_id": result[1]}

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


def parse_title(input):
    title = input.strip()
    errors = []

    if not title:
        errors.append("Title must not be blank.")
    if len(title) > 50:
        errors.append("Title must not be longer than 50 characters")

    return title, errors


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
    sql = "DELETE FROM Recipes WHERE id = ?"
    db.execute(sql, [id])
    db.commit()


def next_ingredient_number(recipe_id):
    sql = "SELECT MAX(ingredient_number) FROM RecipeIngredients WHERE recipe_id = ?"
    result = database.query_db(sql, [recipe_id], one=True)
    if result is None or result[0] is None:
        return 1

    return result[0] + 1


def parse_ingredient(input):
    ingredient = input.strip()
    errors = []

    if not ingredient:
        errors.append("Ingredient must not be empty.")
    if len(ingredient) > 100:
        errors.append("Ingredient must not be longer than 100 characters.")

    return ingredient, errors


def new_ingredient(recipe_id, content):
    number = next_ingredient_number(recipe_id)
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


def next_instruction_number(recipe_id):
    sql = "SELECT MAX(instruction_number) FROM RecipeInstructions WHERE recipe_id = ?"
    result = database.query_db(sql, [recipe_id], one=True)
    if result is None or result[0] is None:
        return 1

    return result[0] + 1


def parse_instruction(input):
    instruction = input.strip()
    errors = []

    if not instruction:
        errors.append("Instruction must not be empty.")
    if len(instruction) > 2000:
        errors.append("Instruction must not be longer than 2000 characters.")


def new_instruction(recipe_id, content):
    number = next_instruction_number(recipe_id)
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
