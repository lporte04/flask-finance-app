from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Account, User
from app.forms import FinancialSetupForm

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/dashboard')
@login_required
def view():
    account = current_user.accounts.first()
    form = FinancialSetupForm(obj=account)

    return render_template('dashboard.html', form=form, account_exists=bool(account))

