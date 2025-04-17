from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from datetime import datetime
from app import db
from forms import LoginForm, RequestPasswordResetForm, ResetPasswordForm, ChangePasswordForm
from models import User
from services import AuthService
from utils import log_action, admin_required
from models import ActionType

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))

        if not user.is_active:
            flash('This account has been deactivated. Please contact an administrator.', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)
        AuthService.login_user(user, db)

        # Redirect to the page the user was trying to access
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            if user.role.value == 'admin':
                next_page = url_for('admin.dashboard')
            else:
                next_page = url_for('main.index')

        return redirect(next_page)

    return render_template('auth/login.html', title='Log In', form=form)


@auth.route('/logout')
@login_required
def logout():
    AuthService.logout_user(current_user, db)
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect', 'danger')
            return redirect(url_for('auth.change_password'))

        current_user.set_password(form.new_password.data)
        db.session.commit()
        log_action(ActionType.UPDATE, "Changed password", db)

        flash('Your password has been updated!', 'success')
        return redirect(url_for('main.index'))

    return render_template('auth/change_password.html', title='Change Password', form=form)


@auth.route('/reset-password-request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # In a real application, we would send an email with a reset token
            # For this demo, we'll just show a success message
            flash('Check your email for instructions to reset your password', 'info')
        else:
            flash('Email not found', 'danger')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password_request.html', title='Reset Password', form=form)


@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    # In a real application, we would verify the token and get the user
    # For this demo, we'll just show a form but it won't actually work
    form = ResetPasswordForm()
    if form.validate_on_submit():
        flash('Your password has been reset!', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', title='Reset Password', form=form)