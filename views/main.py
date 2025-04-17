from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app import db
from models import UserRole
from utils import role_required

main = Blueprint('main', __name__)


@main.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == UserRole.ADMIN:
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == UserRole.COMPANY_OWNER:
            return redirect(url_for('main.owner_dashboard'))
        elif current_user.role == UserRole.MANAGER:
            return redirect(url_for('main.manager_dashboard'))
        elif current_user.role == UserRole.OPERATOR:
            return redirect(url_for('main.operator_dashboard'))
        elif current_user.role == UserRole.DRIVER:
            return redirect(url_for('main.driver_dashboard'))

    return render_template('index.html', title='Welcome to CRM')


@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', title='My Profile')


@main.route('/dashboard/owner')
@login_required
@role_required(UserRole.COMPANY_OWNER.value)
def owner_dashboard():
    # In a complete application, we would fetch data related to the owner's company
    return render_template('owner/dashboard.html', title='Company Owner Dashboard')


@main.route('/dashboard/manager')
@login_required
@role_required(UserRole.MANAGER.value)
def manager_dashboard():
    # In a complete application, we would fetch data related to the manager's teams
    return render_template('manager/dashboard.html', title='Manager Dashboard')


@main.route('/dashboard/operator')
@login_required
@role_required(UserRole.OPERATOR.value)
def operator_dashboard():
    # In a complete application, we would fetch data related to the operator's tasks
    return render_template('operator/dashboard.html', title='Operator Dashboard')


@main.route('/dashboard/driver')
@login_required
@role_required(UserRole.DRIVER.value)
def driver_dashboard():
    # In a complete application, we would fetch data related to the driver's routes
    return render_template('driver/dashboard.html', title='Driver Dashboard')