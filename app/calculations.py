from datetime import date
from sqlalchemy.orm import Session
from models import User, Account, RecurringExpense, Spending, SavingsGoal

class BudgetManager:
    def __init__(self, db_session: Session, account_id: int):
        self.db = db_session
        self.account = self.db.query(Account).filter_by(id=account_id).one()

    def calculate_weekly_income(self) -> float:
        if self.account.hourly_wage and self.account.hours_per_week:
            return self.account.hourly_wage * self.account.hours_per_week
        return 0.0

    def calculate_weekly_expenses(self) -> float:
        total = 0
        expenses = self.account.expenses
        for exp in expenses:
            if exp.frequency == 'weekly':
                total += exp.amount
            elif exp.frequency == 'monthly':
                total += exp.amount / 4  # Roughly 4 weeks in a month
            elif exp.frequency == 'daily':
                total += exp.amount * 7  # 7 days a week
        return total

    def calculate_weekly_spendable(self) -> float:
        return max(0, self.calculate_weekly_income() - self.calculate_weekly_expenses())

    def week_update(self):
        available = self.calculate_weekly_spendable()
        self.account.current_balance += available

        self.db.commit()

    def make_personal_spend(self, item_name: str, amount: float):
        if amount > self.account.current_balance:
            raise ValueError("Insufficient funds for this spend.")

        personal_spend = Spending(
            item=item_name,
            amount=amount,
            date=date.today(),
            account_id=self.account.id
        )
        self.db.add(personal_spend)

        self.account.current_balance -= amount
        self.db.commit()

    def weeks_to_save_all(self) -> int:
        backup_balance = self.account.current_balance

        # Backup current spending for goals
        original_spendings = {goal.item: sum(
            spending.amount for spending in self.account.spendings if spending.item == goal.item
        ) for goal in self.account.savings_goals}

        weeks = 0
        while True:
            all_saved = True
            for goal in self.account.savings_goals:
                current_saved = sum(
                    spending.amount for spending in self.account.spendings
                    if spending.item == goal.item
                )
                if current_saved < goal.cost:
                    all_saved = False
                    break
            if all_saved:
                break

            self.simulate_week()
            weeks += 1

        # Restore balance and spending
        self.account.current_balance = backup_balance
        self.db.commit()

        return weeks

    def item_progress_report(self):
        report = []
        for goal in self.account.savings_goals:
            saved_amount = sum(
                spending.amount for spending in self.account.spendings
                if spending.item == goal.item
            )
            progress = (saved_amount / goal.cost) * 100 if goal.cost else 0
            report.append({
                "item": goal.item,
                "saved_amount": saved_amount,
                "target_amount": goal.cost,
                "progress_percent": progress
            })
        return report