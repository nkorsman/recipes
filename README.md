# Recipes app

## Features
- [x] Users can create an account and log in
- [x] Users can add recipes with a title, ingredients and instructions.
- [x] Users can edit and delete their own recipes
- [x] Users can browse and view recipes added by any user
- [x] Recipes can be tagged with one or more categories.
- [x] Users can search recipes by keyword and filter them by category.
- [x] Users can leave comments and ratings on recipes.
- [x] Users can favorite recipes.
- [x] Each user has a profile page that shows their recipes and information about the user

## Usage
First make sure Flask is installed.

Then set up the database
```
$ sqlite3 database.db < schema.sql
```

You can then run the app with
```
flask run
```

## Large amounts of data
The app uses pagination and database indexes to be able to handle large amounts of data. Running `seed.py` adds
- 100 thousand users,
- 10 thousand tags,
- 1 million recipes,
- roughly 4 million reviews
- and roughly 4 million favorited recipes

to the database. Running the seed script with these settings takes around 6 minutes on my machine.

Here is a comparison of page load times before and after adding indexes:

- Loading the homepage: 2.71 s -> 0.0 s
- Loading the recipe listing: 0.68 s -> 0.08 s
- Loading the tag listing: 2.33 s -> 0.01 s
- Loading a random recipe: 0.33 s -> 0.01 s
- Loading a random user's profile: 0.15 s -> 0.0 s
- Loading a random tag page: 0.45 s -> 0.01 s
- Loading a random recipe's reviews: 0.51 s -> 0.0 s
