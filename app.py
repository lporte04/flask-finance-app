from flask import Flask, render_template, request, jsonify


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# Simulate a temporary data store for now
user_financial_data = []

@app.route('/dashboard')
def dashboard():
    # Get latest entry if available
    latest = user_financial_data[-1] if user_financial_data else None
    calculations = None
    if latest:
        if latest.get('income_type') == 'hourly':
            weekly_income = latest['hourly_wage'] * latest['hours_per_week']
            monthly_income = weekly_income * 4.33
        else:
            weekly_income = latest['income'] / 52
            monthly_income = latest['income'] / 12

        total_expenses = sum(e['cost'] for e in latest['expenses'])
        savings = (weekly_income * 52) - total_expenses
                # Convert weekly and monthly expenses to monthly total
        total_monthly_expenses = 0
        for e in latest['expenses']:
            if e['frequency'] == 'weekly':
                total_monthly_expenses += e['cost'] * 4.33
            elif e['frequency'] == 'monthly':
                total_monthly_expenses += e['cost']

        # Calculate income totals
        yearly_income = weekly_income * 52
        monthly_income = weekly_income * 4.33

        # Calculate available budget after expenses
        account_balance = latest['balance']
        min_balance = latest.get('min_balance', 0)
        free_to_spend = account_balance + yearly_income - (total_monthly_expenses * 12) - min_balance

        calculations = {
            'weekly_income': round(weekly_income, 2),
            'monthly_income': round(monthly_income, 2),
            'yearly_income': round(yearly_income, 2),
            'monthly_expenses': round(total_monthly_expenses, 2),
            'free_to_spend': round(free_to_spend, 2),
            'budget_items': [
                {
                    'name': item['name'],
                    'cost': item['cost'],
                    'progress': f"{min(round((account_balance + yearly_income - min_balance) / item['cost'] * 100, 2), 100)}%",
                    'time_to_save': f"{round(item['cost'] / weekly_income, 1)} weeks" if weekly_income else "-",
                    'display': f"${{min(account_balance + yearly_income - min_balance, item['cost'])}} / ${{item['cost']}}"
                } for item in latest['budget_items']
            ]
        }

    return render_template('dashboard.html', latest=latest, calculations=calculations)

@app.route('/submit_financial_data', methods=['POST'])
def submit_financial_data():
    data = request.json
    user_financial_data.append(data)
    return jsonify({"status": "success"})