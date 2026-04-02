CREATE TABLE Users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT
);

CREATE TABLE Recipes (
    id INTEGER PRIMARY KEY,
    title TEXT,
    author_id INTEGER REFERENCES Users ON DELETE CASCADE
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
)
