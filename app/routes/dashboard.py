from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.models import Account, Spending, SavingsGoal, Investment, Asset
import requests
#imports for income vs expense
from datetime import timedelta, date
from app.calculations import BudgetManager
from app import db

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/dashboard')
@login_required
def view():
    # Get the current user's account
    account = Account.query.filter_by(user_id=current_user.id).first()
    

    if account is None:
        return render_template(
            'dashboard.html',
            net_worth=0,
            assets=[],
            investments=[],
            spendings=[],
            savings_goals=[],
            health_score=0  
        )

    # Assets
    assets = [
        {'name': 'Cash Balance', 'value': account.current_balance},
        *[
            {'name': asset.name, 'value': asset.value}
            for asset in account.assets
        ]
    ]

    # Investments
    investments = account.investments

    # Spendings
    spendings = account.spendings

    # Savings Goals
    savings_goals = account.savings_goals

    # Net Worth Calculation
    total_assets = account.current_balance + sum(asset.value for asset in account.assets)
    total_investments = sum(inv.amount for inv in investments)
    total_spending = sum(s.amount for s in spendings)
    net_worth = total_assets + total_investments - total_spending

    health_score = calculate_health_score(account)


    return render_template(
        'dashboard.html',
        net_worth=net_worth,
        assets=assets,
        investments=investments,
        spendings=spendings,
        savings_goals=savings_goals,
        health_score=health_score
    )

# API for stock history
@dashboard.route('/stock-history')
@login_required
def multi_stock_history():
    symbols = request.args.getlist('symbol') 
    API_KEY = 'L3EONWL3A9WT85W1'

    all_data = {}
    for symbol in symbols:
        url = 'https://www.alphavantage.co/query'
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol,
            'apikey': API_KEY
        }
        r = requests.get(url, params=params)
        data = r.json()

        if 'Time Series (Daily)' not in data:
            continue

        series = data['Time Series (Daily)']
        
        # Convert to a list of dictionaries with date and closing price
        history = [
            {'date': d, 'close': float(v['4. close'])}
            for d, v in sorted(series.items(), reverse=False)
        ]

        # Only get the last 6 months of data (approximately 6 months = 180 days)
        history = history[:180]

        all_data[symbol] = history

    return jsonify(all_data)

#health score
def calculate_health_score(account):
    income = (account.hourly_wage or 0) * (account.hours_per_week or 0) * 4  # approx monthly income
    spending = sum(s.amount or 0 for s in account.spendings)
    savings = sum(goal.current_amount for goal in account.savings_goals)

    if income == 0:
        return 50  # Neutral default

    savings_rate = savings / income if income else 0
    spending_rate = spending / income if income else 0

    score = 50 + (savings_rate * 40) - (spending_rate * 30)
    return int(max(0, min(score, 100)))

#weekly income vs expenses
@dashboard.route('/weekly-summary')
@login_required
def weekly_summary():
    account = Account.query.filter_by(user_id=current_user.id).first()
    if not account:
        return jsonify({'error': 'Unauthorized'}), 403

    bm = BudgetManager(db.session, account.id)

    today = date.today()
    results = []

    for i in range(4):
        end = today - timedelta(days=i * 7)
        start = end - timedelta(days=6)

        weekly_expenses = sum(
            s.amount for s in account.spendings
            if start <= s.date <= end
        )

        weekly_income = bm.calculate_weekly_income()  # static weekly income
        results.append({
            'week': f"{start.strftime('%b %d')} - {end.strftime('%b %d')}",
            'income': round(weekly_income, 2),
            'expenses': round(weekly_expenses, 2)
        })

    results.reverse()  # Make oldest week come first
    return jsonify(results)
