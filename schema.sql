CREATE TABLE Users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);

CREATE TABLE Recipes (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    author_id INTEGER REFERENCES Users ON DELETE CASCADE,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    is_draft INTEGE NOT NULL,

    CHECK (is_draft IN (0, 1))
);

CREATE TABLE Tags (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    recipe_count INTEGER NOT NULL
);

CREATE TABLE Reviews (
    id INTEGER PRIMARY KEY,
    rating INTEGER,
    content TEXT,
    user_id INTEGER NOT NULL REFERENCES Users ON DELETE CASCADE,
    recipe_id INTEGER NOT NULL REFERENCES Recipes ON DELETE CASCADE,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    CHECK (rating BETWEEN 1 AND 5),
    UNIQUE(user_id, recipe_id)
);

CREATE TABLE RecipeIngredients (
    id INTEGER PRIMARY KEY,
    content TEXT NOT NULL,
    ingredient_number INTEGER NOT NULL,
    recipe_id INTEGER NOT NULL REFERENCES Recipes ON DELETE CASCADE,
    UNIQUE(recipe_id, ingredient_number)
);

CREATE TABLE RecipeInstructions (
    id INTEGER PRIMARY KEY,
    content TEXT NOT NULL,
    instruction_number INTEGER NOT NULL,
    recipe_id INTEGER NOT NULL REFERENCES Recipes ON DELETE CASCADE,
    UNIQUE(recipe_id, instruction_number)
);

CREATE TABLE RecipeTags (
    id INTEGER PRIMARY KEY,
    recipe_id INTEGER NOT NULL REFERENCES Recipes ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES Tags ON DELETE CASCADE,
    UNIQUE(recipe_id, tag_id)
);

CREATE TABLE UserFavorites (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES Users ON DELETE CASCADE,
    recipe_id INTEGER NOT NULL REFERENCES Recipes ON DELETE CASCADE,
    UNIQUE(user_id, recipe_id)
);

CREATE INDEX idx_recipes_author_id ON Recipes(author_id);
CREATE INDEX idx_recipes_updated_at ON Recipes(updated_at DESC);

CREATE INDEX idx_reviews_user_id ON Reviews(user_id);
CREATE INDEX idx_reviews_recipe_id ON Reviews(recipe_id);
CREATE INDEX idx_reviews_updated_at ON Reviews(updated_at DESC);

CREATE INDEX idx_recipetags_tag_id ON RecipeTags(tag_id);

CREATE INDEX idx_recipes_recipe_count ON Tags(recipe_count DESC);

CREATE INDEX idx_userfavorites_recipe_id ON UserFavorites(recipe_id);
