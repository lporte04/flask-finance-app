from datetime import date
from app import db
from flask_login import UserMixin

class User(db.Model, UserMixin): # UserMixin is a class from Flask-Login that provides the methods needed for user auth.
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    accounts = db.relationship('Account', backref='owner', lazy=True) # 1-to-many relationship with Account (its here but I dont really think we'll have users with multiple accounts). Backref allows us to access the owner of an account from the account object.

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    current_balance = db.Column(db.Float, nullable=False)
    min_balance_goal = db.Column(db.Float, nullable=False)
    weekly_spending_limit = db.Column(db.Float, nullable=False) # to store how much money the user wants to spend this week. tbd if this is used.
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    hourly_wage = db.Column(db.Float, nullable=True)
    hours_per_week = db.Column(db.Float, nullable=True)
    pay_frequency = db.Column(db.String(10), default="weekly")  # weekly | biweekly
    pay_day_of_week = db.Column(db.Integer, default=4)  # 0=Mon through 6=Sun (Friday default)
    last_pay_credit = db.Column(db.Date, nullable=True)  # Track when last credited

    expenses = db.relationship('RecurringExpense', backref='account', lazy=True, cascade='all, delete-orphan')
    spendings = db.relationship('Spending', backref='account', lazy=True, cascade='all, delete-orphan')
    savings_goals = db.relationship('SavingsGoal', backref='account', lazy=True, cascade='all, delete-orphan')
    investments = db.relationship('Investment', backref='account', lazy=True, cascade='all, delete-orphan')
    assets = db.relationship('Asset', backref='account', lazy=True, cascade='all, delete-orphan')

class RecurringExpense(db.Model): # This is a class to store recurring expenses like rent, subscriptions, etc.
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    frequency = db.Column(db.String(20), nullable=False)  # daily, weekly, monthly. Should probably be using an enum.
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)

class Spending(db.Model): # Tracks purchases made by the user that are not scheduled recurring expenses.
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, default=date.today)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)

class SavingsGoal(db.Model): # Let the user set a savings goal for a specific item.
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(100), nullable=False)
    cost = db.Column(db.Float, nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)

    # This is a relationship to the SavingsDeposit class. It allows us to access all deposits made towards this goal.
    # cascade="all, delete-orphan" means that if a SavingsGoal is deleted, all its associated SavingsDeposits will also be deleted.
    deposits = db.relationship('SavingsDeposit', backref='goal', lazy=True, cascade="all, delete-orphan")
    
    # This is a property that calculates the current amount saved towards the goal by summing up all deposits.
    @property
    def current_amount(self):
        return sum(deposit.amount for deposit in self.deposits)
    
    # This is a property that checks if the goal is funded. It returns True if the current amount is greater than or equal to the cost of the item.
    @property
    def is_funded(self):
        return self.current_amount >= self.cost
    
    #new property to assist in the savings progress bar-sam
    @property
    def progress_percent(self):
        if not self.cost:
            return 0
        return min(100, (self.current_amount / self.cost) * 100)

class SavingsDeposit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, default=date.today)
    savings_goal_id = db.Column(db.Integer, db.ForeignKey('savings_goal.id'), nullable=False)

class Investment(db.Model): # Minimalistic investment tracking. Expand later.
    id = db.Column(db.Integer, primary_key=True)
    stock_name = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False) # Amount invested in the stock.
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)

class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Float, nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)