import sqlite3
from random import choices, randint, sample
from string import ascii_letters

user_count = 100_000
tag_count = 10_000
recipe_count = 1_000_000

db = sqlite3.connect("database.db")
db.execute("PRAGMA foreign_keys = ON")


def distribution():
    n = randint(1, 100)

    if n <= 50:
        return 0
    if n <= 75:
        return randint(1, 3)
    if n <= 90:
        return randint(4, 10)
    if n <= 99:
        return randint(11, 30)

    return randint(31, 100)


def generate_users():
    inserted = 0
    while inserted < user_count:
        username = "".join(choices(ascii_letters, k=randint(1, 20)))
        sql = "INSERT INTO Users (username, password_hash) VALUES (?, ?)"
        try:
            db.execute(sql, [username, "abc"])
        except sqlite3.IntegrityError:
            continue
        inserted += 1
    db.commit()


def generate_tags():
    inserted = 0
    while inserted < tag_count:
        tag_name = "".join(choices(ascii_letters, k=randint(1, 20)))
        sql = "INSERT INTO Tags (name, recipe_count) VALUES (?, 0)"
        try:
            db.execute(sql, [tag_name])
        except sqlite3.IntegrityError:
            continue
        inserted += 1
    db.commit()


def generate_recipes():
    for _ in range(recipe_count):
        title = "".join(choices(ascii_letters, k=randint(1, 50)))
        author_id = randint(1, user_count)

        sql = """INSERT INTO Recipes (title, author_id, created_at, updated_at, is_draft)
                VALUES (?, ?, DATETIME('now'), DATETIME('now'), 0)"""
        row = db.execute(sql, [title, author_id])
        recipe_id = row.lastrowid

        for j in range(randint(1, 20)):
            random_string = "".join(choices(ascii_letters, k=randint(1, 100)))
            sql = """INSERT INTO RecipeIngredients
                    (content, ingredient_number, recipe_id)
                    VALUES (?, ?, ?)"""
            db.execute(sql, [random_string, j, recipe_id])

        for j in range(randint(1, 20)):
            random_string = "".join(choices(ascii_letters, k=randint(1, 1000)))
            sql = """INSERT INTO RecipeInstructions
                    (content, instruction_number, recipe_id)
                    VALUES (?, ?, ?)"""
            db.execute(sql, [random_string, j, recipe_id])

        for j in range(randint(0, 10)):
            tag_id = randint(1, tag_count)
            sql = "INSERT INTO RecipeTags (recipe_id, tag_id) VAlUES (?, ?)"
            try:
                db.execute(sql, [recipe_id, tag_id])
                sql = "UPDATE Tags SET recipe_count = recipe_count + 1 WHERE id = ?"
                db.execute(sql, [tag_id])
            except sqlite3.IntegrityError:
                continue

    db.commit()


def generate_reviews():
    for i in range(1, recipe_count + 1):
        count = distribution()
        user_ids = sample(range(1, user_count + 1), count)
        for j in user_ids:
            content = "".join(choices(ascii_letters, k=randint(1, 500)))
            rating = randint(1, 5)
            sql = """INSERT INTO Reviews (recipe_id, user_id, rating, content, created_at, updated_at)
                     VALUES (?, ?, ?, ?, DATETIME('now'), DATETIME('now'))"""
            db.execute(sql, [i, j, rating, content])
    db.commit()


def generate_favorites():
    for i in range(1, recipe_count + 1):
        count = distribution()
        user_ids = sample(range(1, user_count + 1), count)
        for j in user_ids:
            sql = "INSERT INTO UserFavorites (user_id, recipe_id) VALUES (?, ?)"
            db.execute(sql, [j, i])
    db.commit()


generate_users()
generate_tags()
generate_recipes()
generate_reviews()
generate_favorites()
