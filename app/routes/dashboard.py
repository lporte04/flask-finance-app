from datetime import date, timedelta
import requests

from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user

# ---- UI-branch models & helpers ----
from app.models import Account, Spending, SavingsGoal, Investment, Asset
from app.calculations import BudgetManager

# ---- Form-branch services & forms ----
from app.forms import FinancialForm, SavingsDepositForm
from app.services import account as account_svc
from app.services import deposits as deposit_svc
from app import db

dashboard = Blueprint("dashboard", __name__)

# ---------------------
#  MAIN DASHBOARD VIEW
# ---------------------
@dashboard.route("/dashboard")
@login_required
def view():
    # get the account
    account = account_svc.get_or_create_account(current_user.id)

    assets = (
        [{'name': 'Cash Balance', 'value': account.current_balance}]
        + [{'name': a.name, 'value': a.value} for a in account.assets]
    )

    investments   = account.investments
    spendings     = account.spendings
    savings_goals = account.savings_goals

    total_assets       = account.current_balance + sum(a.value for a in account.assets)
    total_investments  = sum(inv.amount for inv in investments)
    total_spending     = sum(s.amount for s in spendings)
    net_worth          = total_assets + total_investments - total_spending
    health_score       = calculate_health_score(account)

    # ----- modal forms -----
    finance_form     = FinancialForm(obj=account)
    deposit_form = SavingsDepositForm()
    account_svc.prefill_financial_form(finance_form, account)
    deposit_form.goal_id.choices = [
        (g.id, f"{g.item} (${g.cost - g.current_amount:.2f} remaining)")
        for g in savings_goals
    ]

    return render_template(
        "dashboard.html",
        # visual data
        net_worth=net_worth,
        assets=assets,
        investments=investments,
        spendings=spendings,
        savings_goals=savings_goals,
        health_score=health_score,
        # modal data
        form=finance_form,
        deposit_form=deposit_form,
        account_exists=bool(account.expenses or account.savings_goals),
        today=date.today().strftime("%Y-%m-%d"),
    )


# ---------------------
#  FORM ENDPOINTS
# ---------------------
@dashboard.post("/dashboard/save")
@login_required
def save_financial():
    form = FinancialForm()
    if not form.validate_on_submit():
        for field, errs in form.errors.items():
            for err in errs:
                flash(f"{field}: {err}", "danger")
        return redirect(url_for(".view"))

    account = account_svc.get_or_create_account(current_user.id)
    
    account.current_balance = form.current_balance.data
    account.min_balance_goal = form.min_balance_goal.data
    account.hourly_wage = form.hourly_wage.data
    account.hours_per_week = form.hours_per_week.data

    # complex lists
    account_svc.sync_financial_form(form, account)

    db.session.commit()
    flash("Financial information saved!", "success")
    return redirect(url_for(".view"))

@dashboard.post("/dashboard/save_deposit")
@login_required
def save_deposit():
    form = SavingsDepositForm()

    # get the account and populate the choices before validation or it will fail
    account = account_svc.get_or_create_account(current_user.id)
    form.goal_id.choices = [(g.id, g.item) for g in account.savings_goals]

    if not form.validate_on_submit():
        flash("Invalid data", "danger")
        return redirect(url_for(".view"))

    try:
        deposit_svc.create_deposit(form.goal_id.data, form.amount.data)
        flash("Deposit added!", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for(".view"))

# ---------------------
#  API ENDPOINTS
# ---------------------

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

#health score helper
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