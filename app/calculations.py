from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.models import User, Account, RecurringExpense, Spending, SavingsGoal, SavingsDeposit

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

    def make_personal_spend(self, item_name: str, amount: float, today=None):
        '''Make a personal spend and update the account balance accordingly.'''
        today = today or date.today()

        if amount > self.account.current_balance:
            raise ValueError(f"Insufficient funds for '{item_name}'. You need ${amount:.2f} but have only ${self.account.current_balance:.2f}.")

        personal_spend = Spending(
            item=item_name,
            amount=amount,
            date=today,
            account_id=self.account.id
        )
        self.db.add(personal_spend)

        self.account.current_balance -= amount
        self.db.commit()

        return personal_spend

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

    def calculate_net_worth(self) -> float:
        """Calculate user's total net worth"""
        total_assets = self.account.current_balance + sum(a.value for a in self.account.assets)
        total_investments = sum(inv.amount for inv in self.account.investments)
        total_spending = sum(s.amount for s in self.account.spendings)
        return total_assets + total_investments - total_spending
    
    def calculate_health_score(self) -> int:
        """Calculate financial health score (0-100)"""
        income = (self.account.hourly_wage or 0) * (self.account.hours_per_week or 0) * 4
        spending = sum(s.amount or 0 for s in self.account.spendings)
        savings = sum(goal.current_amount for goal in self.account.savings_goals)
        
        if income == 0:
            return 50  # Neutral default
        
        savings_rate = savings / income if income else 0
        spending_rate = spending / income if income else 0
        
        score = 50 + (savings_rate * 40) - (spending_rate * 30)
        return int(max(0, min(score, 100)))
    
    def get_weekly_summary(self, weeks=4) -> list:
        """Get weekly income vs expenses for the past several weeks"""
        today = date.today()
        results = []
        
        for i in range(weeks):
            end = today - timedelta(days=i * 7)
            start = end - timedelta(days=6)
            
            weekly_expenses = sum(
                s.amount for s in self.account.spendings
                if start <= s.date <= end
            )
            
            weekly_income = self.calculate_weekly_income()
            results.append({
                'week': f"{start.strftime('%b %d')} - {end.strftime('%b %d')}",
                'income': round(weekly_income, 2),
                'expenses': round(weekly_expenses, 2)
            })
        
        return list(reversed(results))  # Make oldest week come first
    
    def credit_payday_if_due(self, today=None):
        """Credit wages on the user's scheduled payday"""
        # If no custom date is provided, use today's date. this is for admin simulation purposes.
        today = today or date.today()
        acc = self.account
        
        # Check if today is the user's payday. weekday() returns 0 for monday, 1 for tuesday, etc
        if today.weekday() != acc.pay_day_of_week:
            return False # Exit if today is not the user's payday
        
        # Check if we already credited this pay cycle
        cycle_days = 14 if acc.pay_frequency == "biweekly" else 7
        if acc.last_pay_credit and (today - acc.last_pay_credit).days < cycle_days:
            return False # Exit if we already credited this pay cycle
        
        # Calculate and credit payment
        weekly_income = self.calculate_weekly_income()
        # If biweekly, double the payment amount
        payment = weekly_income * 2 if acc.pay_frequency == "biweekly" else weekly_income
        
        acc.current_balance += payment
        acc.last_pay_credit = today
        self.db.commit()
        
        return True