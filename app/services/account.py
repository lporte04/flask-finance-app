# app/services/account.py
from app import db
from app.models import (Account, RecurringExpense, SavingsGoal, Spending, Asset, Investment)

__all__ = [ # Define the public API of this module (what will be imported when using 'from module import *')
    "get_or_create_account",
    "prefill_financial_form",
    "sync_financial_form",
]

def get_or_create_account(user_id: int) -> Account:
    """return the user's single Account, creating an empty one if needed."""
    account = Account.query.filter_by(user_id=user_id).first()
    if account is None:
        account = Account(
            user_id=user_id, 
            current_balance=0.0,        # Add default value for current_balance to meet the NOT NULL constraint
            min_balance_goal=0.0,       # Add default value for min_balance_goal to meet the NOT NULL constraint
            weekly_spending_limit=0.0,  # Add default value for weekly_spending_limit to meet the NOT NULL constraint
        )
        db.session.add(account)
        db.session.flush()          # flush so row gets primary key without committing. Need this for FKs and for form to work.
    return account

def prefill_financial_form(form, account):
    """copy model data to WTForm so it shows existing data."""
    # clear existing data in each FieldList (subform) inside the main form
    for field_list in (form.expenses, form.goals, form.spendings,
                       form.assets, form.investments):
        field_list.entries = []

    # copy data from model to form for each FieldList
    for exp in account.expenses:
        row = form.expenses.append_entry()
        row.form.id.data = exp.id
        row.form.name.data = exp.name
        row.form.amount.data = exp.amount
        row.form.frequency.data = exp.frequency

    for goal in account.savings_goals:
        row = form.goals.append_entry()
        row.form.id.data = goal.id
        row.form.item.data = goal.item
        row.form.cost.data = goal.cost

    for spend in account.spendings:
        row = form.spendings.append_entry()
        row.form.id.data = spend.id
        row.form.item.data = spend.item
        row.form.amount.data = spend.amount
        row.form.date.data = spend.date

    for asset in account.assets:
        row = form.assets.append_entry()
        row.form.id.data = asset.id
        row.form.name.data = asset.name
        row.form.value.data = asset.value

    for inv in account.investments:
        row = form.investments.append_entry()
        row.form.id.data = inv.id
        row.form.stock_name.data = inv.stock_name
        row.form.amount.data = inv.amount


def _upsert_collection(rows, model_cls, account: Account):
    """
    private helper performing list-diff synchronisation (create, update, delete):
        UPDATE: Existing records (with an id) are updated with new values
        INSERT: New records (without an id) are created
        DELETE: Records in the database that aren't in the incoming rows are removed

    this function tracks which rows are seen and deletes any that aren't in the incoming data.

    Args:
        rows - list of dictionaries coming from WTForms FieldList
        model_cls - SQLAlch model class to write to (e.g. RecurringExpense)
        account - parent Account instance (used for FK & filtering)
    """
    seen = [] # list of IDs that are seen in the incoming data
    for row in rows:
        row_id = row.get("id")
        payload = {k: v for k, v in row.items() # payload is a dict containing only the model columns (attributes to be stored in the DB), discarding the id and csrf_token
                   if k not in ("id", "csrf_token")}

        # update existing records
        if row_id and row_id.strip(): # check if exists and is not empty
            item = model_cls.query.get(int(row_id)) # fetch existing record by id
            if item and item.account_id == account.id: # verify item exists, belongs to current account, update each attribute with values from payload
                for k, v in payload.items():
                    setattr(item, k, v) # assigns obj.name = value dynamically
                seen.append(item.id) # add to seen list to prevent deletion
        # insert new records
        else:
            item = model_cls(**payload) # create new instance of model with payload data (** to unpack dict)
            item.account = account # set relationship to account
            db.session.add(item) # add new item to DB session
            db.session.flush() # flush to get ID for new record (without commiting)
            seen.append(item.id) # add to seen list to prevent deletion

    # delete orphan records
    for item in model_cls.query.filter_by(account_id=account.id):
        if item.id not in seen:
            db.session.delete(item)


def sync_financial_form(form, account: Account) -> None:
    """persist all FieldLists in one go."""
    _upsert_collection(form.expenses.data, RecurringExpense, account)
    _upsert_collection(form.goals.data, SavingsGoal, account)
    _upsert_collection(form.spendings.data, Spending, account)
    _upsert_collection(form.assets.data, Asset, account)
    _upsert_collection(form.investments.data, Investment, account)
