from flask_wtf import FlaskForm
from wtforms import Form, StringField, PasswordField, SubmitField, FloatField, SelectField, FormField, DateField, HiddenField, FieldList
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, NumberRange, Optional
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
    amount   = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0)])
    frequency= SelectField('Frequency', choices=[('daily','Daily'),
                                                ('weekly','Weekly'),
                                                ('monthly','Monthly')], validators=[DataRequired()])

class _GoalEntry(Form):
    id   = HiddenField()
    item = StringField('Goal', validators=[DataRequired(), Length(max=100)])
    cost = FloatField('Cost', validators=[DataRequired(), NumberRange(min=0)])

class _SpendingEntry(Form):
    id     = HiddenField()
    item   = StringField('Item', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0)])
    date   = DateField('Date', format='%Y-%m-%d', default=date.today, validators=[DataRequired()])

class _AssetEntry(Form):
    id    = HiddenField()
    name  = StringField('Asset Name', validators=[DataRequired(), Length(max=100)])
    value = FloatField('Value', validators=[DataRequired(), NumberRange(min=0)])

class _InvestmentEntry(Form):
    id         = HiddenField()
    stock_name = StringField('Stock Name', validators=[DataRequired(), Length(max=50)])
    amount     = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0)])

# master form / account form
class FinancialForm(FlaskForm):
    current_balance = FloatField('Current Balance', validators=[DataRequired(), NumberRange(min=0)])
    min_balance_goal= FloatField('Minimum Balance Goal', validators=[Optional(), NumberRange(min=0)])
    hourly_wage     = FloatField('Hourly Wage', validators=[DataRequired(), NumberRange(min=0)])
    hours_per_week  = FloatField('Hours / Week', validators=[DataRequired(), NumberRange(min=0)])

    expenses = FieldList(FormField(_ExpenseEntry), min_entries=0)
    goals = FieldList(FormField(_GoalEntry), min_entries=0)
    spendings = FieldList(FormField(_SpendingEntry), min_entries=0)
    assets = FieldList(FormField(_AssetEntry), min_entries=0)
    investments = FieldList(FormField(_InvestmentEntry), min_entries=0)

    submit = SubmitField('Save')

class SavingsDepositForm(FlaskForm):
    """Form for adding a single deposit to a savings goal"""
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    goal_id = SelectField('Savings Goal', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Make Deposit')
