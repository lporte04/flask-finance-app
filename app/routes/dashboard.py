from datetime import date, timedelta
import requests

from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash, session, current_app
from flask_login import login_required, current_user

# ---- UI-branch models & helpers ----
from app.models import Account, Spending, SavingsGoal, Investment, Asset
from app.calculations import BudgetManager

# ---- Form-branch services & forms ----
from app.forms import FinancialForm, SavingsDepositForm
from app.services import account as account_svc
from app.services import deposits as deposit_svc
from app.services import dashboard_data as dashboard_svc
from app.services import expense_processor as expense_svc
from app.utilities.date_utils import get_effective_date
from app import db

dashboard = Blueprint("dashboard", __name__)

# ---------------------
#  MAIN DASHBOARD VIEW
# ---------------------
@dashboard.route("/dashboard")
@login_required
def view():
    # Get the effective date (with any simulation offset)
    effective_date = get_effective_date()

    # Get the account
    account = account_svc.get_or_create_account(current_user.id)

    # Process payday credit
    bm = BudgetManager(db.session, account.id)
    credited = bm.credit_payday_if_due(effective_date)
    if credited:
        flash(f"Payday! Your wages have been credited to your account.", "success")
    
    # Process any recurring expenses that should be added to spending records today
    expense_svc.process_recurring_expenses(account, effective_date)

    # Get dashboard data using the service
    data = dashboard_svc.get_dashboard_data(account)
    
    # Set up forms
    finance_form = FinancialForm(obj=account)
    deposit_form = SavingsDepositForm()
    account_svc.prefill_financial_form(finance_form, account)
    
    if data['savings_goals']:
        deposit_form.goal_id.choices = [
            (g.id, f"{g.item} (${g.cost - g.current_amount:.2f} remaining)")
            for g in data['savings_goals']
        ]
    
    return render_template(
        "dashboard.html",
        # Pass all dashboard data
        **data,
        # Modal data
        form=finance_form,
        deposit_form=deposit_form,
        account_exists=bool(account.expenses or account.savings_goals),
        today=effective_date.strftime("%Y-%m-%d"),
        simulated_date=effective_date.strftime("%B-%d-%Y"),
        account=account
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
    account.pay_frequency = form.pay_frequency.data
    account.pay_day_of_week = int(form.pay_day_of_week.data)

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
    account = account_svc.get_or_create_account(current_user.id)
        
    bm = BudgetManager(db.session, account.id)
    data = bm.get_weekly_summary(4)
    return jsonify(data)

@dashboard.route('/api/max-spend')
@login_required
def max_spend_api():
    account = account_svc.get_or_create_account(current_user.id)
    
    # return current balance as max spendable amount
    available = account.current_balance
    
    return jsonify({"max": round(available, 2)})

# ---------------------
#  ADMIN-ONLY TIME SIMULATION ENDPOINTS
# ---------------------

@dashboard.post("/dashboard/simulate_date")
@login_required
def simulate_date():
    # Only allow admin users
    if current_user.email != current_app.config['ADMIN_EMAIL']:
        flash("Not authorized", "danger")
        return redirect(url_for('.view'))
        
    days = int(request.form.get('days_offset', 0))
    current_offset = session.get('date_simulation_offset', 0)
    session['date_simulation_offset'] = current_offset + days
    
    flash(f"Simulated {days} days into the future", "info")
    return redirect(url_for('.view'))

@dashboard.post("/dashboard/reset_date")
@login_required
def reset_date():
    # Only allow admin users
    if current_user.email != current_app.config['ADMIN_EMAIL']:
        flash("Not authorized", "danger")
        return redirect(url_for('.view'))
        
    session.pop('date_simulation_offset', None)
    flash("Reset to current date", "info")
    return redirect(url_for('.view'))

@dashboard.post("/dashboard/reset_pay_credit")
@login_required
def reset_pay_credit():
    # Only allow admin users
    if current_user.email != current_app.config['ADMIN_EMAIL']:
        flash("Not authorized", "danger")
        return redirect(url_for('.view'))
        
    # Get account and reset last_pay_credit
    account = account_svc.get_or_create_account(current_user.id)
    account.last_pay_credit = None
    db.session.commit()
    
    flash("Last pay credit date has been reset", "success")
    return redirect(url_for('.view'))