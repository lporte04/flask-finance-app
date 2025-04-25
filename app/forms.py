from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, NumberRange, Optional
from app.models import User


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

class FinancialSetupForm(FlaskForm):
    current_balance = FloatField('Current Balance', validators=[DataRequired(), NumberRange(min=0)])
    min_balance_goal = FloatField('Minimum Balance Goal', validators=[Optional(), NumberRange(min=0)])
    hourly_wage = FloatField('Hourly Wage', validators=[DataRequired(), NumberRange(min=0)])
    hours_per_week = FloatField('Hours Worked Per Week', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Save')