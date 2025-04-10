# app.py
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

from extensions import db, login_manager
from models import User, Expense, Budget

from flask_login import LoginManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expense_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            flash('Username or email already exists!', 'error')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registered successfully. Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    budgets = Budget.query.filter_by(user_id=current_user.id).all()

    # Total savings calculation
    total_budget = sum(b.amount for b in budgets)
    total_spent = sum(e.amount for e in expenses)
    total_savings = total_budget - total_spent

    # Prepare category-wise data
    categories = []
    category_names = set([b.category for b in budgets])

    for category_name in category_names:
        budget_amount = sum(b.amount for b in budgets if b.category == category_name)
        spent_amount = sum(e.amount for e in expenses if e.category == category_name)
        percentage = round((spent_amount / budget_amount) * 100, 2) if budget_amount else 0

        categories.append({
            'name': category_name,
            'budget': budget_amount,
            'spent': spent_amount,
            'percentage': percentage
        })

    return render_template(
        'dashboard.html',
        total_budget=total_budget,
        total_spent=total_spent,
        total_savings=total_savings,
        categories=categories,
        transactions=expenses
    )


@app.route('/add-expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    categories = ['Food', 'Transport', 'Utilities', 'Entertainment', 'Health', 'Others']

    if request.method == 'POST':
        category = request.form['category']
        amount = float(request.form['amount'])
        date = datetime.strptime(request.form['date'], '%Y-%m-%d')
        description = request.form.get('description', '')

        new_expense = Expense(
            user_id=current_user.id,
            category=category,
            amount=amount,
            date=date,
            description=description
        )

        db.session.add(new_expense)
        db.session.commit()
        flash('Expense added successfully.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_expense.html', categories=categories, datetime=datetime)


@app.route('/manage-budgets', methods=['GET', 'POST'])
@login_required
def manage_budgets():
    from datetime import datetime  # just in case not imported
    if request.method == 'POST':
        category = request.form['category']
        amount = float(request.form['amount'])
        month = int(request.form['month'])
        year = int(request.form['year'])
        threshold = float(request.form['alert_threshold'])

        budget = Budget(user_id=current_user.id, category=category, amount=amount,
                        month=month, year=year, alert_threshold=threshold)
        db.session.add(budget)
        db.session.commit()
        flash('Budget saved successfully.', 'success')
        return redirect(url_for('manage_budgets'))

    budgets = Budget.query.filter_by(user_id=current_user.id).all()
    total_budget = sum(b.amount for b in budgets)

    return render_template(
        'manage_budgets.html',
        budgets=budgets,
        total_budget=total_budget,
        current_year=datetime.now().year
    )



@app.route('/reports')
@login_required
def reports():
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    expenses = Expense.query.filter_by(user_id=current_user.id).all()

    monthly_total = sum(
        expense.amount for expense in expenses
        if expense.date.month == current_month and expense.date.year == current_year
    )

    category_totals = {}
    for expense in expenses:
        if expense.date.month == current_month and expense.date.year == current_year:
            category_totals[expense.category] = category_totals.get(expense.category, 0) + expense.amount

    return render_template(
        'reports.html',
        total=monthly_total,
        categories=category_totals,
        current_month=current_month,
        current_year=current_year,
        datetime=datetime  )


@app.route('/shared-expenses')
@login_required
def shared_expenses():
    return render_template('shared_expenses.html')

@app.context_processor
def inject_global_data():
    if current_user.is_authenticated:
        budgets = Budget.query.filter_by(user_id=current_user.id).all()
        expenses = Expense.query.filter_by(user_id=current_user.id).all()
        
        total_budget = sum(b.amount for b in budgets)
        total_spent = sum(e.amount for e in expenses)
        
        return dict(total_budget=total_budget, total_spent=total_spent)
    
    return dict(total_budget=0, total_spent=0)


@app.errorhandler(Exception)
def handle_exception(e):
    return f"<h1>Something went wrong</h1><pre>{str(e)}</pre>", 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
