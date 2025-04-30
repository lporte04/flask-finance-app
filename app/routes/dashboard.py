from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.forms import FinancialForm, SavingsDepositForm
from app.services import account as account_svc
from app.services import deposits as deposit_svc
from app import db                       # needed only for flush in svc

dashboard = Blueprint("dashboard", __name__)

@dashboard.route("/dashboard")
@login_required
def view():
    account   = account_svc.get_or_create_account(current_user.id)
    form      = FinancialForm(obj=account)
    deposit_form  = SavingsDepositForm()

    # fill dropdown and FieldLists
    account_svc.prefill_financial_form(form, account)
    deposit_form.goal_id.choices = [
        (g.id, f"{g.item} (${g.cost-g.current_amount:.2f} remaining)")
        for g in account.savings_goals
    ]

    return render_template(
        "dashboard.html",
        form=form,
        deposit_form=deposit_form,
        account_exists=bool(account.expenses or account.savings_goals),
        today=date.today().strftime("%Y-%m-%d"),
    )

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