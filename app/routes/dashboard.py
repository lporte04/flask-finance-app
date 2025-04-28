from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Account, Spending, SavingsGoal, Investment, RecurringExpense
#imports for alphavantage API
import requests
from flask import jsonify, request

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


#API
@dashboard.route('/stock-history')
@login_required
def multi_stock_history():
    symbols = request.args.getlist('symbol')  # ?symbol=AAPL&symbol=GOOG&symbol=MSFT
    API_KEY = 'YOUR_ALPHA_VANTAGE_API_KEY'

    all_data = {}
    for symbol in symbols:
        url = 'https://www.alphavantage.co/query'
        params = {
            'function': 'TIME_SERIES_DAILY_ADJUSTED',
            'symbol': symbol,
            'apikey': API_KEY
        }
        r = requests.get(url, params=params)
        data = r.json()

        if 'Time Series (Daily)' not in data:
            continue

        series = data['Time Series (Daily)']
        history = [
            {'date': d, 'close': float(v['4. close'])}
            for d, v in sorted(series.items(), reverse=False)
        ][:30]

        all_data[symbol] = history

    print(all_data)
    return jsonify(all_data)

