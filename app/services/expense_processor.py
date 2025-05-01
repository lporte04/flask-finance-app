from datetime import date, timedelta
from app import db
from app.models import Spending

def process_recurring_expenses(account, custom_date=None):
    """
    Processes recurring expenses by creating Spending records based on frequency.

    Args:
        account: Account object to process expenses for
        custom_date: Optional date override for simulation purposes
    """
    today = custom_date or date.today()
    
    for expense in account.expenses:
        # For each expense, determine if we need to create a spending record
        if expense.frequency == 'daily':
            _process_daily_expense(expense, account, today)
        elif expense.frequency == 'weekly':
            _process_weekly_expense(expense, account, today)
        elif expense.frequency == 'monthly':
            _process_monthly_expense(expense, account, today)
    
    # Commit all new spending records at once
    db.session.commit()

def _process_daily_expense(expense, account, today):
    """Process a daily recurring expense"""
    # Check if there's already a spending record for this expense today
    existing = Spending.query.filter_by(
        item=f"Recurring: {expense.name}",
        account_id=account.id,
        date=today
    ).first()
    
    if not existing:
        spending = Spending(
            item=f"Recurring: {expense.name}",
            amount=expense.amount,
            date=today,
            account_id=account.id
        )
        db.session.add(spending)

def _process_weekly_expense(expense, account, today):
    """Process a weekly recurring expense (on Mondays)"""
    if today.weekday() == 0:  # Monday
        # Check if there's already a spending record for this expense this week
        start_of_week = today
        end_of_week = today + timedelta(days=6)
        
        # Ensure we only create one spending record for the week
        # Check if there's already a spending record for this expense this week
        existing = Spending.query.filter(
            Spending.item == f"Recurring: {expense.name}",
            Spending.account_id == account.id,
            Spending.date >= start_of_week,
            Spending.date <= end_of_week
        ).first()
        
        if not existing:
            spending = Spending(
                item=f"Recurring: {expense.name}",
                amount=expense.amount,
                date=today,
                account_id=account.id
            )
            db.session.add(spending)

def _process_monthly_expense(expense, account, today):
    """Process a monthly recurring expense (on last day of month)"""
    # Check if today is the last day of the month by starting from the 28th, adding 4 days, and then subtracting the number of days in that month
    # this will work for all months, including february and will give us the last day of the month.
    next_month = today.replace(day=28) + timedelta(days=4)
    last_day = (next_month - timedelta(days=next_month.day)).day
    
    if today.day == last_day:
        # Check if there's already a spending record for this expense this month
        month_start = today.replace(day=1)
        
        # Ensure we only create one spending record for the month
        # Check if there's already a spending record for this expense this month
        existing = Spending.query.filter(
            Spending.item == f"Recurring: {expense.name}",
            Spending.account_id == account.id,
            Spending.date >= month_start,
            Spending.date <= today
        ).first()
        
        if not existing:
            spending = Spending(
                item=f"Recurring: {expense.name}",
                amount=expense.amount,
                date=today,
                account_id=account.id
            )
            db.session.add(spending)