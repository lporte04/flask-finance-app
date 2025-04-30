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
    
    return {
        'net_worth': net_worth,
        'assets': assets,
        'investments': account.investments,
        'spendings': account.spendings,
        'savings_goals': account.savings_goals,
        'health_score': health_score,
        'weekly_summary': bm.get_weekly_summary(4)
    }