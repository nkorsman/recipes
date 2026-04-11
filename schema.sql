CREATE TABLE Users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT
);

CREATE TABLE Recipes (
    id INTEGER PRIMARY KEY,
    title TEXT,
    author_id INTEGER REFERENCES Users ON DELETE CASCADE,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE Tags (
    id INTEGER PRIMARY KEY,
    name TEXT
);

CREATE TABLE RecipeIngredients (
    id INTEGER PRIMARY KEY,
    content TEXT,
    ingredient_number INTEGER,
    recipe_id INTEGER REFERENCES Recipes ON DELETE CASCADE,
    UNIQUE(recipe_id, ingredient_number)
);

CREATE TABLE RecipeInstructions (
    id INTEGER PRIMARY KEY,
    content TEXT,
    instruction_number INTEGER,
    recipe_id INTEGER REFERENCES Recipes ON DELETE CASCADE,
    UNIQUE(recipe_id, instruction_number)
);

CREATE TABLE RecipeTags (
    id INTEGER PRIMARY KEY,
    recipe_id INTEGER REFERENCES Recipes ON DELETE CASCADE,
    tag_id INTEGER REFERENCES Tags ON DELETE CASCADE,
    UNIQUE(recipe_id, tag_id)
);

CREATE TABLE UserFavorites (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES Users ON DELETE CASCADE,
    recipe_id INTEGER REFERENCES Recipes ON DELETE CASCADE,
    UNIQUE(user_id, recipe_id)
);
