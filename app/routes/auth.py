from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models.user import User
from app.models.audit import AuditLog
from datetime import datetime
import random, string

auth_bp = Blueprint('auth', __name__)

def generate_member_id():
    return 'MEM' + ''.join(random.choices(string.digits, k=6))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password) and user.is_active:
            login_user(user, remember=request.form.get('remember'))
            AuditLog.log(user.id, 'LOGIN', ip=request.remote_addr)
            flash(f'Welcome back, {user.name}!', 'success')
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('student.dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register'))
        user = User(
            name=name, email=email,
            password=generate_password_hash(password),
            member_id=generate_member_id(),
            role='student', joined_date=datetime.utcnow()
        )
        db.session.add(user)
        db.session.commit()
        AuditLog.log(user.id, 'REGISTER', ip=request.remote_addr)
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    AuditLog.log(current_user.id, 'LOGOUT', ip=request.remote_addr)
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))