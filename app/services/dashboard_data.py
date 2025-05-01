from app.calculations import BudgetManager
from app import db

def get_dashboard_data(account):
    """Get all data needed for dashboard display"""
    # Create budget manager for calculations
    bm = BudgetManager(db.session, account.id)
    
    # assets data
    assets = [{'name': 'Cash Balance', 'value': account.current_balance}]
    for asset in account.assets:
        assets.append({'name': asset.name, 'value': asset.value})
    
    balance = account.current_balance

    # calculate metrics
    net_worth = bm.calculate_net_worth()
    health_score = bm.calculate_health_score()

    # Calculate difference from minimum balance goal
    # If None or 0, that means no goal is set, so diff should be None
    if account.min_balance_goal is None or account.min_balance_goal == 0:
        diff = None
    else:
        diff = balance - account.min_balance_goal

    if diff is None:
        bal_status = "No balance goal set"
    elif diff >= 0:
        bal_status = f"You are ${diff:.2f} above your minimum balance goal."
    else:
        bal_status = f"You are ${abs(diff):.2f} below your minimum balance goal."

    # sort spendings by date (newest first)
    sorted_spendings = sorted(account.spendings, key=lambda s: (s.date, s.id), reverse=True)

    # Filter purchased goals out from the dashboard display
    active_goals = [goal for goal in account.savings_goals if not goal.purchased]
    
    return {
        'net_worth': net_worth,
        'balance': balance,
        'balance_status': bal_status,
        'assets': assets,
        'investments': account.investments,
        'spendings': sorted_spendings,
        'savings_goals': active_goals,
        'health_score': health_score,
        'weekly_summary': bm.get_weekly_summary(4)
    }