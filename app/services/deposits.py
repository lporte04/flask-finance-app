from datetime import date
from app import db
from app.models import SavingsGoal, SavingsDeposit, Spending
from app.utilities.date_utils import get_effective_date
from flask import flash

def create_deposit(goal_id: int, amount: float):
    """Create a deposit that validates against balance and reduces account funds."""
    if amount <= 0:
        raise ValueError("Deposit amount must be greater than zero.")

    goal = SavingsGoal.query.get(goal_id)
    if not goal:
        raise ValueError("Goal not found")
    
    # Get account and validate balance
    account = goal.account
    if amount > account.current_balance:
        raise ValueError(f"Insufficient funds. Need ${amount:.2f}, have ${account.current_balance:.2f}")
    
    # Check if deposit would exceed goal cost
    remaining_needed = goal.cost - goal.current_amount
    if amount > remaining_needed:
        original_amount = amount
        amount = remaining_needed
        flash(f"Amount adjusted from ${original_amount:.2f} to ${amount:.2f} to complete the goal.", "info")
    
    # Create deposit with effective date
    deposit = SavingsDeposit(
        amount=amount,
        date=get_effective_date(),
        goal=goal
    )
    
    # Reduce account balance
    account.current_balance -= amount
    db.session.add(deposit)
    
    # If goal is now fully funded, create a spending record (without reducing balance again)
    # This avoids double counting the spending since the deposit already reduced the balance
    # We avoid this by not using the BudgetManager here, as it would reduce the balance again
    if goal.is_funded and not goal.purchased:
        spending = Spending(
            item=f"Purchase: {goal.item}",
            amount=goal.cost,
            date=get_effective_date(),
            account_id=account.id
        )

        # mark goal as purchased and set purchase date
        goal.purchased = True
        goal.purchase_date = get_effective_date()

        db.session.add(spending)
        flash(f"Congratulations! Your goal '{goal.item}' is now fully funded and has been marked as purchased!", "success")
    
    db.session.commit()
    return deposit