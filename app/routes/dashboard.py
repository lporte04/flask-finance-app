from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Account, Spending, SavingsGoal, Investment, RecurringExpense

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/dashboard')
@login_required
def view():

    #return render_template('dashboard.html')

    ##generated code to get data on dashboard

    account = Account.query.filter_by(user_id=current_user.id).first()

    if account is None:
        return render_template(
        'dashboard.html',
        net_worth=0,
        assets=[],
        investments=[],
        spendings=[],
        savingsgoal=[]
        )



    assets = [
        {'name': 'Cash Balance', 'value': account.current_balance},
    ]


    # Investments
    investments = [
        {'stock_name': inv.stock_name, 'amount': 1000}  # Placeholder until you add 'amount' to Investment model
        for inv in account.investments
    ]


    # Spendings
    spendings = [
        {'item': s.item, 'amount': s.amount, 'date': s.date.strftime('%Y-%m-%d')}
        for s in account.spendings
    ]


    # Savings goals
    savingsgoal = [
        {'name': g.item, 'amount': g.cost}
        for g in account.savings_goals
    ]


    # Net worth = current_balance + total investments - total spendings
    total_assets = account.current_balance
    total_investments = sum([1000 for _ in account.investments])  # adjust when Investment has amount
    total_spending = sum(s.amount for s in account.spendings)
    net_worth = total_assets + total_investments - total_spending


    return render_template(
        'dashboard.html',
        net_worth=net_worth,
        assets=assets,
        investments=investments,
        spendings=spendings,
        savingsgoal=savingsgoal
    )

