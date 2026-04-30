import sqlite3
from random import choices, randint
from string import ascii_letters

db = sqlite3.connect("database.db")
db.execute("PRAGMA foreign_keys = ON")

for i in range(100):
    title = f"Recipe {i}"
    author_id = 1

    sql = """INSERT INTO Recipes (title, author_id, created_at, updated_at, is_draft)
             VALUES (?, ?, DATETIME('now'), DATETIME('now'), 0)"""
    row = db.execute(sql, [title, author_id])
    recipe_id = row.lastrowid

    for j in range(randint(3, 15)):
        random_string = "".join(choices(ascii_letters, k=randint(4, 20)))
        sql = """INSERT INTO RecipeIngredients
                 (content, ingredient_number, recipe_id)
                 VALUES (?, ?, ?)"""
        db.execute(sql, [random_string, j, recipe_id])

    for j in range(randint(3, 15)):
        random_string = "".join(choices(ascii_letters, k=randint(20, 300)))
        sql = """INSERT INTO RecipeInstructions
                 (content, instruction_number, recipe_id)
                 VALUES (?, ?, ?)"""
        db.execute(sql, [random_string, j, recipe_id])

    db.commit()
