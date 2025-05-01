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
    
    # calculate metrics
    net_worth = bm.calculate_net_worth()
    health_score = bm.calculate_health_score()

    # sort spendings by date (newest first)
    sorted_spendings = sorted(account.spendings, key=lambda s: s.date, reverse=True)

    # Filter purchased goals out from the dashboard display
    active_goals = [goal for goal in account.savings_goals if not goal.purchased]
    
    return {
        'net_worth': net_worth,
        'assets': assets,
        'investments': account.investments,
        'spendings': sorted_spendings,
        'savings_goals': active_goals,
        'health_score': health_score,
        'weekly_summary': bm.get_weekly_summary(4)
    }