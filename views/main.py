from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import or_, func

from app import db
from models import UserRole, User, Manager, Operator, Driver, Company, CompanyOwner
from models import Task, TaskStatus, Route, RouteStatus, ActionType, Log
from utils import role_required, log_action
from forms import CompanyForm, UserForm, EditUserForm

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
    """
    Dashboard for company owner with analytics and stats
    """
    if not current_user.company_owner or not current_user.company_owner.company_id:
        flash('You are not associated with a company.', 'danger')
        return redirect(url_for('main.index'))

    company_id = current_user.company_owner.company_id
    company = Company.query.get(company_id)

    # Get team statistics
    manager_count = Manager.query.filter_by(company_id=company_id).count()
    operator_count = Operator.query.filter_by(company_id=company_id).count()
    driver_count = Driver.query.filter_by(company_id=company_id).count()
    team_count = manager_count + operator_count + driver_count

    # Get task statistics
    task_query = Task.query.filter_by(company_id=company_id)
    task_count = task_query.count()
    completed_tasks = task_query.filter_by(status=TaskStatus.COMPLETED).count()
    in_progress_tasks = task_query.filter_by(status=TaskStatus.IN_PROGRESS).count()
    new_tasks = task_query.filter_by(status=TaskStatus.NEW).count()
    active_tasks = in_progress_tasks + new_tasks

    # Get route statistics
    route_query = Route.query.filter_by(company_id=company_id)
    route_count = route_query.count()
    completed_routes = route_query.filter_by(status=RouteStatus.COMPLETED).count()
    in_progress_routes = route_query.filter_by(status=RouteStatus.IN_PROGRESS).count()
    planned_routes = route_query.filter_by(status=RouteStatus.PLANNED).count()
    active_routes = in_progress_routes + planned_routes

    # Calculate efficiency score (simplified example)
    if task_count > 0:
        completion_rate = (completed_tasks / task_count) * 100
    else:
        completion_rate = 0

    if route_count > 0:
        route_completion_rate = (completed_routes / route_count) * 100
    else:
        route_completion_rate = 0

    # Simple efficiency calculation
    efficiency_score = int((completion_rate + route_completion_rate) / 2) if task_count > 0 and route_count > 0 else 0

    # Get recent logs
    recent_logs = Log.query.filter_by(company_id=company_id).order_by(Log.timestamp.desc()).limit(5).all()

    log_action(ActionType.VIEW, "Viewed owner dashboard", db.session)

    return render_template(
        'owner/dashboard.html',
        title='Company Owner Dashboard',
        company=company,
        manager_count=manager_count,
        operator_count=operator_count,
        driver_count=driver_count,
        team_count=team_count,
        task_count=task_count,
        completed_tasks=completed_tasks,
        in_progress_tasks=in_progress_tasks,
        new_tasks=new_tasks,
        active_tasks=active_tasks,
        route_count=route_count,
        completed_routes=completed_routes,
        in_progress_routes=in_progress_routes,
        planned_routes=planned_routes,
        active_routes=active_routes,
        efficiency_score=efficiency_score,
        recent_logs=recent_logs
    )


@main.route('/dashboard/owner/managers')
@login_required
@role_required(UserRole.COMPANY_OWNER.value)
def owner_managers():
    """
    Managers list for company owner
    """
    if not current_user.company_owner or not current_user.company_owner.company_id:
        flash('You are not associated with a company.', 'danger')
        return redirect(url_for('main.index'))

    company_id = current_user.company_owner.company_id
    page = request.args.get('page', 1, type=int)

    # Get all managers for this company
    managers_query = Manager.query.filter_by(company_id=company_id)

    # Order by name
    managers_query = managers_query.join(User, Manager.id == User.id).order_by(User.first_name, User.last_name)

    # Paginate results
    managers = managers_query.paginate(page=page, per_page=10)

    log_action(ActionType.VIEW, "Viewed managers list", db.session)

    return render_template(
        'owner/managers.html',
        title='Company Managers',
        managers=managers
    )


@main.route('/dashboard/owner/managers/add', methods=['GET', 'POST'])
@login_required
@role_required(UserRole.COMPANY_OWNER.value)
def add_manager():
    """
    Add a new manager
    """
    if not current_user.company_owner or not current_user.company_owner.company_id:
        flash('You are not associated with a company.', 'danger')
        return redirect(url_for('main.index'))

    company_id = current_user.company_owner.company_id

    # Create form
    form = UserForm()
    form.role.data = UserRole.MANAGER.value

    if form.validate_on_submit():
        try:
            # Create user with manager role
            user = User(
                username=form.username.data,
                email=form.email.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                phone=form.phone.data,
                role=UserRole.MANAGER,
                is_active=form.is_active.data
            )

            # Set password
            user.set_password(form.password.data)

            # Handle profile image if provided
            if form.profile_image.data:
                from utils import save_profile_image
                user.profile_image = save_profile_image(form.profile_image.data)

            db.session.add(user)
            db.session.flush()  # Get user ID

            # Create manager relationship with company
            manager = Manager(id=user.id, company_id=company_id)
            db.session.add(manager)

            db.session.commit()
            log_action(ActionType.CREATE, f"Created manager {user.username}", db)

            flash(f'Manager {user.first_name} {user.last_name} created successfully!', 'success')
            return redirect(url_for('main.owner_managers'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating manager: {str(e)}', 'danger')

    return render_template(
        'owner/add_manager.html',
        title='Add New Manager',
        form=form,
        UserRole=UserRole
    )


@main.route('/dashboard/owner/managers/<int:manager_id>/view')
@login_required
@role_required(UserRole.COMPANY_OWNER.value)
def view_manager(manager_id):
    """
    View manager details including their team and performance
    """
    if not current_user.company_owner or not current_user.company_owner.company_id:
        flash('You are not associated with a company.', 'danger')
        return redirect(url_for('main.index'))

    company_id = current_user.company_owner.company_id

    # Get manager
    manager = Manager.query.get_or_404(manager_id)

    # Ensure manager belongs to owner's company
    if manager.company_id != company_id:
        flash('You do not have permission to view this manager.', 'danger')
        return redirect(url_for('main.owner_managers'))

    # Get manager's team (operators)
    operators = manager.operators

    # Count drivers under this manager's operators
    driver_count = Driver.query.join(Operator, Driver.operator_id == Operator.id) \
        .filter(Operator.manager_id == manager_id).count()

    # Calculate performance metrics
    # This would typically be calculated from task completion rates, etc.
    # For demo purposes, we'll use sample data
    tasks = Task.query.filter(
        Task.company_id == company_id,
        Task.creator_id == manager.id
    ).all()

    task_count = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
    in_progress_tasks = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)

    # Calculate completion rate
    completion_rate = f"{round((completed_tasks / task_count) * 100) if task_count > 0 else 0}%"

    # Get routes associated with this manager's team
    routes = Route.query.join(Driver, Route.driver_id == Driver.id) \
        .join(Operator, Driver.operator_id == Operator.id) \
        .filter(Operator.manager_id == manager_id).all()

    on_time_deliveries = 0
    total_routes = len(routes)

    for route in routes:
        if route.status == RouteStatus.COMPLETED and route.end_time and route.start_time:
            # Simplified on-time calculation (should include estimated time in real app)
            estimated_time = route.estimated_time or 120  # 2 hours default
            actual_time = (route.end_time - route.start_time).total_seconds() / 60
            if actual_time <= estimated_time * 1.1:  # 10% buffer
                on_time_deliveries += 1

    on_time_rate = f"{round((on_time_deliveries / total_routes) * 100) if total_routes > 0 else 0}%"

    # Get available operators for assignment
    available_operators = Operator.query.filter_by(company_id=company_id).all()

    log_action(ActionType.VIEW, f"Viewed manager {manager.user.first_name} {manager.user.last_name}", db.session)

    return render_template(
        'owner/view_manager.html',
        title=f'Manager: {manager.user.first_name} {manager.user.last_name}',
        manager=manager,
        driver_count=driver_count,
        task_count=task_count,
        completed_tasks=completed_tasks,
        in_progress_tasks=in_progress_tasks,
        completion_rate=completion_rate,
        on_time_rate=on_time_rate,
        available_operators=available_operators
    )


@main.route('/dashboard/owner/managers/<int:manager_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(UserRole.COMPANY_OWNER.value)
def edit_manager(manager_id):
    """
    Edit manager details
    """
    if not current_user.company_owner or not current_user.company_owner.company_id:
        flash('You are not associated with a company.', 'danger')
        return redirect(url_for('main.index'))

    company_id = current_user.company_owner.company_id

    # Get manager
    manager = Manager.query.get_or_404(manager_id)

    # Ensure manager belongs to owner's company
    if manager.company_id != company_id:
        flash('You do not have permission to edit this manager.', 'danger')
        return redirect(url_for('main.owner_managers'))

    # Create form
    form = EditUserForm(
        original_username=manager.user.username,
        original_email=manager.user.email
    )

    if request.method == 'GET':
        form.username.data = manager.user.username
        form.email.data = manager.user.email
        form.first_name.data = manager.user.first_name
        form.last_name.data = manager.user.last_name
        form.phone.data = manager.user.phone
        form.is_active.data = manager.user.is_active

    if form.validate_on_submit():
        try:
            # Update user details
            manager.user.username = form.username.data
            manager.user.email = form.email.data
            manager.user.first_name = form.first_name.data
            manager.user.last_name = form.last_name.data
            manager.user.phone = form.phone.data
            manager.user.is_active = form.is_active.data

            # Handle profile image if provided
            if form.profile_image.data:
                from utils import save_profile_image
                manager.user.profile_image = save_profile_image(form.profile_image.data)

            db.session.commit()
            log_action(ActionType.UPDATE, f"Updated manager {manager.user.username}", db.session)

            flash(f'Manager {manager.user.first_name} {manager.user.last_name} updated successfully!', 'success')
            return redirect(url_for('main.view_manager', manager_id=manager_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating manager: {str(e)}', 'danger')

    return render_template(
        'owner/edit_manager.html',
        title='Edit Manager',
        form=form,
        manager=manager
    )


@main.route('/dashboard/owner/managers/<int:manager_id>/delete', methods=['POST'])
@login_required
@role_required(UserRole.COMPANY_OWNER.value)
def delete_manager(manager_id):
    """
    Delete a manager
    """
    if not current_user.company_owner or not current_user.company_owner.company_id:
        flash('You are not associated with a company.', 'danger')
        return redirect(url_for('main.index'))

    company_id = current_user.company_owner.company_id

    # Get manager
    manager = Manager.query.get_or_404(manager_id)

    # Ensure manager belongs to owner's company
    if manager.company_id != company_id:
        flash('You do not have permission to delete this manager.', 'danger')
        return redirect(url_for('main.owner_managers'))

    # Check if manager has operators
    if manager.operators:
        flash('Cannot delete manager with assigned operators. Please reassign operators first.', 'danger')
        return redirect(url_for('main.view_manager', manager_id=manager_id))

    try:
        # Get user for log
        username = manager.user.username
        user_id = manager.user.id

        # Delete the manager (and user cascade)
        db.session.delete(manager.user)
        db.session.commit()

        log_action(ActionType.DELETE, f"Deleted manager {username}", db.session)
        flash(f'Manager {username} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting manager: {str(e)}', 'danger')

    return redirect(url_for('main.owner_managers'))


@main.route('/dashboard/owner/managers/<int:manager_id>/assign-operators', methods=['POST'])
@login_required
@role_required(UserRole.COMPANY_OWNER.value)
def assign_operators_to_manager(manager_id):
    """
    Assign operators to a manager
    """
    if not current_user.company_owner or not current_user.company_owner.company_id:
        flash('You are not associated with a company.', 'danger')
        return redirect(url_for('main.index'))

    company_id = current_user.company_owner.company_id

    # Get manager
    manager = Manager.query.get_or_404(manager_id)

    # Ensure manager belongs to owner's company
    if manager.company_id != company_id:
        flash('You do not have permission to modify this manager.', 'danger')
        return redirect(url_for('main.owner_managers'))

    # Get selected operator IDs
    operator_ids = request.form.getlist('operator_ids[]')

    try:
        # Get all operators for this company
        company_operators = Operator.query.filter_by(company_id=company_id).all()

        # Update manager assignments
        for operator in company_operators:
            if str(operator.id) in operator_ids:
                # Assign to this manager
                operator.manager_id = manager_id
            elif operator.manager_id == manager_id:
                # Unassign from this manager
                operator.manager_id = None

        db.session.commit()
        log_action(ActionType.UPDATE, f"Updated operator assignments for manager {manager.user.username}", db.session)

        flash('Operator assignments updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating operator assignments: {str(e)}', 'danger')

    return redirect(url_for('main.view_manager', manager_id=manager_id))


@main.route('/dashboard/owner/operators/<int:operator_id>/remove-from-manager/<int:manager_id>', methods=['POST'])
@login_required
@role_required(UserRole.COMPANY_OWNER.value)
def remove_operator_from_manager(operator_id, manager_id):
    """
    Remove an operator from a manager
    """
    if not current_user.company_owner or not current_user.company_owner.company_id:
        flash('You are not associated with a company.', 'danger')
        return redirect(url_for('main.index'))

    company_id = current_user.company_owner.company_id

    # Get operator and manager
    operator = Operator.query.get_or_404(operator_id)
    manager = Manager.query.get_or_404(manager_id)

    # Ensure they belong to owner's company
    if operator.company_id != company_id or manager.company_id != company_id:
        flash('You do not have permission to modify these users.', 'danger')
        return redirect(url_for('main.owner_managers'))

    # Ensure operator is assigned to this manager
    if operator.manager_id != manager_id:
        flash('This operator is not assigned to the specified manager.', 'warning')
        return redirect(url_for('main.view_manager', manager_id=manager_id))

    try:
        # Remove manager assignment
        operator.manager_id = None
        db.session.commit()

        log_action(ActionType.UPDATE, f"Removed operator {operator.user.username} from manager {manager.user.username}",
                   db)
        flash(f'Operator {operator.user.first_name} {operator.user.last_name} removed from manager successfully!',
              'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error removing operator from manager: {str(e)}', 'danger')

    return redirect(url_for('main.view_manager', manager_id=manager_id))


@main.route('/dashboard/owner/company-settings')
@login_required
@role_required(UserRole.COMPANY_OWNER.value)
def owner_company_settings():
    """
    Company settings page for owner
    """
    if not current_user.company_owner or not current_user.company_owner.company_id:
        flash('You are not associated with a company.', 'danger')
        return redirect(url_for('main.index'))

    company_id = current_user.company_owner.company_id
    company = Company.query.get(company_id)

    # Get team statistics
    manager_count = Manager.query.filter_by(company_id=company_id).count()
    operator_count = Operator.query.filter_by(company_id=company_id).count()
    driver_count = Driver.query.filter_by(company_id=company_id).count()
    total_team_count = manager_count + operator_count + driver_count

    # Get mock company settings
    # In a real app, this would be from a settings table
    company_settings = {
        'enable_notifications': True,
        'task_assignment_approval': False,
        'allow_driver_messaging': True,
        'auto_route_optimization': False,
        'default_task_deadline': 24
    }

    log_action(ActionType.VIEW, "Viewed company settings", db.session)

    return render_template(
        'owner/company_settings.html',
        title='Company Settings',
        company=company,
        manager_count=manager_count,
        operator_count=operator_count,
        driver_count=driver_count,
        total_team_count=total_team_count,
        company_settings=company_settings
    )


@main.route('/dashboard/owner/edit-company', methods=['GET', 'POST'])
@login_required
@role_required(UserRole.COMPANY_OWNER.value)
def edit_company():
    """
    Edit company details
    """
    if not current_user.company_owner or not current_user.company_owner.company_id:
        flash('You are not associated with a company.', 'danger')
        return redirect(url_for('main.index'))

    company_id = current_user.company_owner.company_id
    company = Company.query.get(company_id)

    # Create form
    form = CompanyForm()

    if request.method == 'GET':
        form.name.data = company.name
        form.legal_name.data = company.legal_name
        form.tax_id.data = company.tax_id
        form.address.data = company.address
        form.phone.data = company.phone
        form.email.data = company.email
        form.website.data = company.website

    if form.validate_on_submit():
        try:
            # Update company details
            company.name = form.name.data
            company.legal_name = form.legal_name.data
            company.tax_id = form.tax_id.data
            company.address = form.address.data
            company.phone = form.phone.data
            company.email = form.email.data
            company.website = form.website.data

            db.session.commit()
            log_action(ActionType.UPDATE, f"Updated company details for {company.name}", db.session)

            flash('Company details updated successfully!', 'success')
            return redirect(url_for('main.owner_company_settings'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating company details: {str(e)}', 'danger')

    return render_template(
        'owner/edit_company.html',
        title='Edit Company',
        form=form,
        company=company
    )


@main.route('/dashboard/owner/update-company-settings', methods=['POST'])
@login_required
@role_required(UserRole.COMPANY_OWNER.value)
def update_company_settings():
    """
    Update company settings
    """
    if not current_user.company_owner or not current_user.company_owner.company_id:
        flash('You are not associated with a company.', 'danger')
        return redirect(url_for('main.index'))

    # In a real app, this would update a settings table
    # For this demo, we'll just acknowledge the update

    enable_notifications = 'enable_notifications' in request.form
    task_assignment_approval = 'task_assignment_approval' in request.form
    allow_driver_messaging = 'allow_driver_messaging' in request.form
    auto_route_optimization = 'auto_route_optimization' in request.form
    default_task_deadline = int(request.form.get('default_task_deadline', 24))

    # Log the settings update
    settings_summary = f"Notifications: {enable_notifications}, " \
                       f"Task Approval: {task_assignment_approval}, " \
                       f"Driver Messaging: {allow_driver_messaging}, " \
                       f"Route Optimization: {auto_route_optimization}, " \
                       f"Default Deadline: {default_task_deadline}h"

    log_action(ActionType.UPDATE, f"Updated company settings: {settings_summary}", db.session)

    flash('Company settings updated successfully!', 'success')
    return redirect(url_for('main.owner_company_settings'))