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
from app.utilities.form_utils import flash_form_errors
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
            (g.id, f"{g.item} - ${g.current_amount:.2f} / ${g.cost:.2f} ({g.progress_percent:.0f}%)")
            for g in data['savings_goals'] if not g.is_funded
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
        flash_form_errors(form)
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
        for field, errors in form.errors.items():
            for error in errors:
                field_name = getattr(form, field).label.text  # Get the human-readable field name
                flash(f"{field_name}: {error}", "danger")
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
@dashboard.route('/stock-history-yahoo')
@login_required
def yahoo_stock_history():
    """Use Yahoo Finance instead of Alpha Vantage"""
    symbols = request.args.getlist('symbol')
    
    # Add caching logic to reduce API calls
    cache_key = f"yahoo_stock_data_{'_'.join(sorted(symbols))}"
    cached_data = session.get(cache_key)
    
    # Return cached data if available and not expired (cache for 7 days)
    if cached_data and cached_data.get('timestamp', 0) > (date.today().toordinal() - 7):
        return jsonify(cached_data['data'])
    
    all_data = {}
    try:
        for symbol in symbols:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            params = {
                'interval': '1wk',  # weekly data
                'range': '6mo'      # 6 months
            }
            
            r = requests.get(url, params=params, headers=headers, timeout=10)
            data = r.json()
            
            # Parse Yahoo Finance data format
            if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                result = data['chart']['result'][0]
                timestamps = result['timestamp']
                quotes = result['indicators']['quote'][0]
                
                history = []
                for i, ts in enumerate(timestamps):
                    if 'close' in quotes and quotes['close'][i] is not None:
                        # Convert timestamp to date format
                        dt = date.fromtimestamp(ts)
                        history.append({
                            'date': dt.isoformat(),
                            'close': quotes['close'][i]
                        })
                
                all_data[symbol] = history
            else:
                all_data[f'{symbol}_error'] = "No data available from Yahoo Finance"
                
        # Cache the results
        session[cache_key] = {
            'timestamp': date.today().toordinal(),
            'data': all_data
        }
                
    except Exception as e:
        all_data['error'] = f"Failed to fetch data: {str(e)}"
        
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

@dashboard.route('/api/max-deposit')
@login_required
def max_deposit_api():
    account = account_svc.get_or_create_account(current_user.id)
    
    # maximum deposit is total available balance
    available = account.current_balance
    
    # safe deposit is amount above minimum balance goal. Handles case wher no goal is set.
    min_goal = account.min_balance_goal or 0
    safe_amount = max(0, account.current_balance - min_goal)
    
    return jsonify({
        "max": round(available, 2),
        "safe": round(safe_amount, 2)
    })

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