from datetime import date
from app import db
from app.models import SavingsGoal, SavingsDeposit

def create_deposit(goal_id: int, amount: float):
    """create a new deposit for a savings goal and save it to the database."""
    goal = SavingsGoal.query.get(goal_id)
    if not goal:
        raise ValueError("Goal not found")

    deposit = SavingsDeposit(amount=amount, date=date.today(), goal=goal)
    db.session.add(deposit)
    db.session.commit()
    return deposit