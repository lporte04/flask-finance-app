from flask_wtf import FlaskForm
from wtforms import Form, StringField, PasswordField, SubmitField, FloatField, SelectField, FormField, DateField, HiddenField, FieldList
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, NumberRange, Optional, InputRequired
from app.models import User
from datetime import date


class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first() # Check if email already exists in DB
        if user:
            raise ValidationError('This email is already in use. Please choose a different email.')

class LoginForm(FlaskForm): # Consider adding "remember me" functionality later
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# subforms
class _ExpenseEntry(Form):
    id       = HiddenField()                      # Prefilled when editing
    name     = StringField('Expense', validators=[DataRequired(), Length(min=2, max=100)])
    amount = FloatField('Amount', validators=[
        InputRequired(message="Please enter an amount."),
        NumberRange(min=0.01, message="Expense amount must be greater than zero.")
    ])
    frequency= SelectField('Frequency', choices=[('daily','Daily'),
                                                ('weekly','Weekly'),
                                                ('monthly','Monthly')], validators=[DataRequired()])

class _GoalEntry(Form):
    id   = HiddenField()
    item = StringField('Goal', validators=[DataRequired(), Length(max=100)])
    cost = FloatField('Cost', validators=[
        InputRequired(message="Please enter a cost."),
        NumberRange(min=0.01, message="Goal cost must be greater than zero.")
    ])

class _SpendingEntry(Form):
    id     = HiddenField()
    item   = StringField('Item', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[
        InputRequired(message="Please enter an amount."),
        NumberRange(min=0.01, message="Spending amount must be greater than zero.")
    ])
    date   = DateField('Date', format='%Y-%m-%d', default=date.today, validators=[DataRequired()])

class _AssetEntry(Form):
    id    = HiddenField()
    name  = StringField('Asset Name', validators=[DataRequired(), Length(max=100)])
    value = FloatField('Value', validators=[
        InputRequired(message="Please enter a value."),
        NumberRange(min=0.01, message="Asset value must be greater than zero.")
    ])

class _InvestmentEntry(Form):
    id         = HiddenField()
    stock_name = StringField('Stock Name', validators=[DataRequired(), Length(max=50)])
    amount     = FloatField('Amount', validators=[
        InputRequired(message="Please enter an amount."),
        NumberRange(min=0.01, message="Investment amount must be greater than zero.")
    ])

# master form / account form
class FinancialForm(FlaskForm):
    current_balance = FloatField('Current Balance', validators=[
        InputRequired(message="Please enter your current balance."),
        NumberRange(min=0, message="Balance cannot be negative.")
    ])
    min_balance_goal= FloatField('Minimum Balance Goal', validators=[Optional(), NumberRange(min=0)])
    hourly_wage = FloatField('Hourly Wage', validators=[
        InputRequired(message="Please enter your hourly wage."),
        NumberRange(min=0.01, message="Hourly wage must be greater than zero.")
    ])
    hours_per_week = FloatField('Hours / Week', validators=[
        InputRequired(message="Please enter your weekly hours."),
        NumberRange(min=0.01, message="Hours worked must be greater than zero.")
    ])
    pay_frequency = SelectField(
        "Pay Frequency", 
        choices=[("weekly", "Weekly"), ("biweekly", "Bi-Weekly")],
        default="weekly"
    )
    # Using list comprehension to: loop through the days of the week and generate index #'s with enumerate()
    # for each iteration, i is the index and d is the day of the week. str() is used to convert the index to a string because WTForms expects string value.
    # and (str(i), d) creates a tuple of the index and the day of the week (ex. [("0", Monday)]). This (value, label) format is the format that WTForms expects for the choices parameter.
    pay_day_of_week = SelectField(
        "Pay-day",
        choices=[(str(i), d) for i, d in enumerate(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])],
        default="4" # Friday
    )

    expenses = FieldList(FormField(_ExpenseEntry), min_entries=0)
    goals = FieldList(FormField(_GoalEntry), min_entries=0)
    spendings = FieldList(FormField(_SpendingEntry), min_entries=0)
    assets = FieldList(FormField(_AssetEntry), min_entries=0)
    investments = FieldList(FormField(_InvestmentEntry), min_entries=0)

    submit = SubmitField('Save')

class SavingsDepositForm(FlaskForm):
    """Form for adding a single deposit to a savings goal"""
    amount = FloatField('Amount', validators=[InputRequired(), NumberRange(min=0.01)])
    goal_id = SelectField('Savings Goal', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Make Deposit')

    