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
