# Table of Contents:
- [Environment Setup](#environment-setup)
  - [Flask Setup/Guide](#flask-setupguide)
  - [Database Setup](#database-setup)
    - [Video Setup](#video-setup)
    - [Steps to follow](#steps-to-follow-if-you-use-datagrip-you-can-watch-the-videos-for-setup-otherwise-find-something-online)
    - [Database Flask Commands](#database-flask-commands)

- [Project Plan/Ideas](#project-planideas)

- [Project Structure Explanation](#project-structure-explanation-based-on-pull-request-2)
  - [Core Python Files](#core-python-files)
  - [Route Files (Blueprint Organization)](#route-files-blueprint-organization)
  - [Templates (Jinja2 Template Files)](#templates-jinja2-template-files)
  - [Database Migration Files](#database-migration-files)
  - [Configuration Files](#configuration-files)
  - [Static Folder](#static)

- [Understanding Jinja2 Templates](#understanding-jinja2-templates)

- [Flask-SQLAlchemy Models](#flask-sqlalchemy-models)

- [Flask-WTF Forms](#flask-wtf-forms)

- [Blueprints](#blueprints)

- [.env Setup](#env-setup)

***

# Enviornment Setup

## Flask Setup/Guide:
[Here is a link to the flask documentation](https://flask.palletsprojects.com/en/stable/)
Flask supports Python 3.9 and newer. (python --version)

1. Create a venv
- For Mac/Linux: run `python3 -m venv .venv` in your project directory
- For Windows: run `py -3 -m venv .venv` in your project directory
2. Activate the venv
- Mac/Linux: `. .venv/bin/activate`
- Windows:  `.venv\Scripts\activate`
3. Inside the venv, run
- `pip install Flask`
4. Install dependencies
- `pip install -r requirements.txt` <- this installs the dependencies listed in requirements.txt. Anytime new dependencies are installed, run `pip freeze > requirements.txt` to update the list of required dependencies.
5. Setup your .env file (minus the database line, since you'll have to do that after setting up the DB)

`flask run --debug` use this to run the app in debug mode, which will auto update the app with any changes you make so you don't have to constantly type the run command. (NOTE: in order for this to work, you need your .env file setup properly)

## Database setup:

[Install Postgres if it's not installed already](https://www.postgresql.org/download/)
**NOTE: When setting up postgres, _write down_ the password you use for your superuser (postgres). Doesn't have to be complicated because you're just using this to run locally. Mine is 123abc**

![image](https://github.com/user-attachments/assets/a7a2ac60-cf01-411f-8d11-f806c3ac80b7)

### Video Setup

Below is a video for how to set up the DB like I did, using [Datagrip](https://www.jetbrains.com/datagrip/). There is a free trial, and students can get a license for free.
- [Postgres and Datagrip setup video](https://www.youtube.com/watch?v=EX81bDA-mkA)
- **You can stop watching the youtube video above once you've downloaded postgres and installed datagrip. The video below will guide you through our application's specific setup from there.**

https://github.com/user-attachments/assets/9c8b2e8a-500f-4cb7-b8ce-4e2e50400982

If you don't want to use Datagrip, there are other apps you can use and you can likely find a tutorial for setting them up.

### Steps to follow (If you use datagrip you can watch the videos for setup, otherwise find something online)

**NOTE: These steps apply to Datagrip or any other software you use for this. There may be different steps in between for setup depending on what you use.**
1. Download postgres
2. Create the database `CREATE DATABASE finance_dashboard;`
3. [Add your database url to the .env file](#2-database_urlpostgresqlpostgres123abclocalhost5432finance_dashboard)
4. Run `flask db upgrade` to create the DB schema
5. You can now register yourself a test user with whatever password and email you want.

### Database flask commands:
- flask db migrate -m "Initial migration"
  -  Use this when you've made a change to the database models (models.py)
- flask db upgrade
  - Use this after pulling code with new migrations and after running `flask db migrate`.

***

# Project Plan/Ideas

## Register/Login Functionalities:
- Consider adding "remember me" feature
- Consider adding "forgot password?" feature

## TODO:
1. ~Implement DB (I forgot something, see #3 of TODO)~
2. ~Implement user logic, ensure register/login and logout functionality~
3. ~DB update: Need to be storing their wages/income (hourly, salary, etc)~
4. Implement dashboard form(s) (Liam)
5. Implement dashboard calculation logic (Liam)
6. Implement dashboard display
7. Implement Investment API (Sam)
8. Implement profile/settings: change login information, profile picture (if we even implement this as a feature), dark mode (if we implement it), etc. (Justice implement dark mode)

***

# Project Structure Explanation (Based on pull request #2):

### Core Python Files

- **run.py**
  - The application entry point
  - Creates the Flask app instance and runs the development server
  - What you execute when starting the application (`flask run` uses this file)

- **config.py**
  - Contains configuration variables for the application
  - Loads environment variables from .env file
  - Sets up database connection and other settings

- **app/__init__.py**
  - Creates the Flask application factory function
  - Initializes Flask extensions (SQLAlchemy, Bcrypt, etc.)
  - Registers blueprints (routes grouped by functionality)
  - Sets up the login manager for authentication

- **app/models.py**
  - Defines database models using SQLAlchemy ORM
  - Contains User, Account, RecurringExpense, Spending, SavingsGoal, and Investment classes
  - Each class represents a table in the database

- **app/forms.py**
  - Creates form classes using Flask-WTF
  - Handles form validation including custom validators
  - Current forms: RegistrationForm and LoginForm

 ### Route Files (Blueprint Organization)

- **app/routes/__init__.py**
  - Empty file that marks the routes directory as a Python package

- **app/routes/main.py**
  - Contains routes for the main pages (just the landing page for now)
  - Currently just has the index route ('/')

- **app/routes/auth.py**
  - Handles all authentication-related routes
  - Manages user registration, login, and logout functionality

- **app/routes/dashboard.py**
  - Contains routes for the dashboard and its features
  - Requires login to access (protected routes)
 
### Templates (Jinja2 Template Files)

- **app/templates/_layout.html**
  - Base template for authenticated pages (dashboard)
  - Contains the sidebar navigation and layout structure
  - Used for pages that require login

- **app/templates/_top-navbar.html**
  - Base template for public-facing pages
  - Contains the top navigation bar
  - Displays different options based on whether user is logged in

- **app/templates/index.html**
  - Landing page template
  - Extends _top-navbar.html

- **app/templates/login.html**
  - Login form page
  - Extends _top-navbar.html

- **app/templates/register.html**
  - Registration form page
  - Extends _top-navbar.html

- **app/templates/dashboard.html**
  - Main dashboard view
  - Will display financial information and analytics
  - Extends _layout.html

### Database Migration Files

- **migrations/**
  - Contains database migration scripts generated by Flask-Migrate
  - Tracks changes to your database schema
  - Allows updating database structure without losing data

- **migrations/versions/**
  - Contains individual migration scripts
  - Each file represents one set of schema changes
  - Current migrations:
    - 48004136e166_initial_migration.py - Created all initial tables
    - 9f2ab928d702_added_hourly_wage_tracking.py - Added hourly wage fields

### Configuration Files

- **.env**
  - Environment variables file (not committed to git)
  - Contains sensitive information like database credentials
  - Also stores configuration like secret keys

- **.gitignore**
  - Lists files and directories that Git should ignore
  - Prevents committing sensitive data, virtual environments, etc.

- **requirements.txt**
  - Lists all Python package dependencies
  - Generated/Updated with `pip freeze > requirements.txt`
  - Used to install dependencies on new environments
 
### static/

- Holds all your static assets – files that don’t change like:

    - css/ – Stylesheets

    - images/ – Logos, icons, etc.

    - scripts/ – JavaScript files

These are accessible in templates using url_for('static', filename='css/styles.css')
 
## Understanding Jinja2 Templates

Jinja2 is the templating engine used by Flask. It allows you to:

### Template Inheritance

```html
{% extends '_layout.html' %}
```
This tells Flask to use _layout.html as the base template and inject this template's content into it.

### Blocks

```html
{% block title %}Dashboard{% endblock %}
```
Define sections that child templates can override. The base template defines these blocks, and child templates fill them in.

### Variable Output

```html
<p>Welcome, {{ current_user.name }}</p>
```
Display dynamic content using double curly braces. Variables are passed from your route functions to the template.

### Control Structures

```html
{% if current_user.is_authenticated %}
  <a href="{{ url_for('auth.logout') }}">Logout</a>
{% else %}
  <a href="{{ url_for('auth.login') }}">Login</a>
{% endif %}
```
Conditionals, loops, and other programming constructs use {% %} syntax.

### URL Generation

```html
<a href="{{ url_for('dashboard.view') }}">Dashboard</a>
```
The `url_for()` function generates URLs based on your route function names, ensuring links stay correct even if routes change.

### Form Handling

```html
<form method="POST" action="{{ url_for('auth.login') }}">
  {{ form.hidden_tag() }}
  {{ form.email.label(class="form-label") }}
  {{ form.email(class="form-control") }}
  {{ form.submit(class="btn btn-primary") }}
</form>
```
Renders form fields from your Flask-WTF forms with proper validation and security features.

### Including Other Templates

```html
{% include 'navbar.html' %}
```
Insert another template file directly into the current template.

## Flask-SQLAlchemy Models

The models.py file defines your database structure:

```python
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # more fields...
    
    # Relationship to other tables
    accounts = db.relationship('Account', backref='owner', lazy=True)
```

Each class becomes a database table, columns become fields, and relationships define how tables connect.

## Flask-WTF Forms

The forms.py file creates web forms with validation:

```python
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
```

Forms handle validation both on the client side and server side, protecting against bad input.

## Blueprints

Routes are organized into blueprints (main, auth, dashboard) which are like mini-applications within your main app. This keeps code organized by feature and prevents circular imports.

## .env setup

Explanations for all of these lines are given below but you can also just copy what I have here in, aside from the DATABASE_URL since that depends on how you setup your database user/pass (if you use the same username and password as me you can just copy it).

```properties
SECRET_KEY='6a1d139d9c1001dbd3b23ddd4697143d'
DATABASE_URL='postgresql://postgres:123abc@localhost:5432/finance_dashboard'
FLASK_APP='run.py'
FLASK_ENV='development'
```

### 1. `SECRET_KEY='6a1d139d9c1001dbd3b23ddd4697143d'`
- **Purpose**: A secret key used by Flask and extensions for security purposes
- Can be generated by doing the following: Create a .env file -> type "python" in your terminal -> type "import secrets" -> type "secrets.token_hex(16) -> type "exit()" -> copy what that gave you into your .env file -> should look like SECRET_KEY='what you got from running the python script' **OR you can just copy mine.**

### 2. `DATABASE_URL='postgresql://postgres:123abc@localhost:5432/finance_dashboard'`
- **Purpose**: Database connection string for PostgreSQL
- **Components**:
  - `postgresql://` - Database driver/type
  - `postgres` - Database username
  - `123abc` - Database password
  - `localhost` - Database server location (your local machine)
  - `5432` - Default PostgreSQL port
  - `finance_dashboard` - Name of your specific database
- **Usage**: Used by SQLAlchemy to establish database connections

### 3. `FLASK_APP='run.py'`
- **Purpose**: Tells Flask which file to use as the application entry point
- **Usage**:
  - When you run `flask run`, it looks for this variable
  - Points to your main application file (`run.py`)
  - This is what lets Flask find your app when running commands like `flask db migrate`

 ### 4. `FLASK_ENV='development'`
- **Purpose**: Sets the environment mode for Flask
- **Effects in development mode**:
  - Enables debug mode (auto-reload when code changes)
  - Shows detailed error pages
  - Enables the Flask debugger
 


