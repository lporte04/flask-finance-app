from datetime import date
from sqlalchemy.orm import Session
from app.models import User, Account, RecurringExpense, Spending, SavingsGoal

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
        return float(total)

    def calculate_weekly_spendable(self) -> float:
        return max(0.00, self.calculate_weekly_income() - self.calculate_weekly_expenses())

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
        backup_available_money = self.available_money
        weeks = 0

        self.available_money = 0  # reset tracker

        goals = sorted(self.account.savings_goals, key=lambda g: g.id)

        while True:
            all_saved = True
            for goal in goals:
                saved_amount = sum(deposit.amount for deposit in goal.deposits)
                if saved_amount < goal.cost:
                    all_saved = False
                    break

            if all_saved:
                break

            self.week_update()

            for goal in goals:
                saved_amount = sum(deposit.amount for deposit in goal.deposits)
                needed = goal.cost - saved_amount
                to_save = min(self.available_money, needed)

                if to_save > 0:
                    deposit = SavingsDeposit(
                        amount=to_save,
                        savings_goal_id=goal.id,
                        date=date.today()
                    )
                    self.db.add(deposit)
                    self.available_money -= to_save

                if self.available_money <= 0:
                    break

            weeks += 1

        self.db.rollback()

        return weeks

    def item_progress_report(self):
        report = []

        for goal in self.account.savings_goals:
            saved_amount = sum(deposit.amount for deposit in goal.deposits)

            progress_percent = (saved_amount / goal.cost) * 100 if goal.cost else 0

            report.append({
                "item": goal.item,
                "saved_amount": round(saved_amount, 2),
                "target_amount": round(goal.cost, 2),
                "progress_percent": round(progress_percent, 2)
            })

        return report

    def get_safe_amount_to_save(self) -> float:

        safe_amount = self.account.current_balance - self.account.min_balance_goal

        return max(safe_amount, 0)

    def save_to_goal(self, goal: SavingsGoal, amount: float):

        safe_amount = self.get_safe_amount_to_save()

        if amount <= 0:
            raise ValueError("Amount to save must be greater than zero.")
        if amount > safe_amount:
            raise ValueError(f"Not enough available funds to save ${amount:.2f} (safe limit: ${safe_amount:.2f}).")

        deposit = SavingsDeposit(
            amount=amount,
            savings_goal_id=goal.id,
            date=date.today()
        )
        self.db.add(deposit)
        self.db.commit()

    def mark_goal_as_purchased(self, goal: SavingsGoal):

        total_saved = sum(deposit.amount for deposit in goal.deposits)

        if total_saved < goal.cost:
            raise ValueError("Goal has not been fully funded yet.")

        spending = Spending(
            item=goal.item,
            amount=goal.cost,
            date=date.today(),
            account_id=self.account.id
        )
        self.db.add(spending)

        for deposit in goal.deposits:
            self.db.delete(deposit)
        self.db.delete(goal)

        self.db.commit()
