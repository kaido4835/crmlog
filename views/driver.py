from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime

from app import db
from models import Route, RouteStatus, User, UserRole, Task, TaskStatus, Driver, Message
from utils import role_required, log_action
from models import ActionType

driver = Blueprint('driver', __name__, url_prefix='/driver')


@driver.route('/dashboard')
@login_required
@role_required('driver')
def routes_dashboard():
    """
    Driver dashboard showing routes
    """
    # Check if user is a driver
    if not current_user.driver:
        flash('This page is only accessible to drivers.', 'danger')
        return redirect(url_for('main.index'))

    # Get driver's routes
    active_route = Route.query.filter_by(
        driver_id=current_user.driver.id,
        status=RouteStatus.IN_PROGRESS
    ).first()

    next_route = Route.query.filter_by(
        driver_id=current_user.driver.id,
        status=RouteStatus.PLANNED
    ).order_by(Route.start_time).first()

    upcoming_routes = Route.query.filter_by(
        driver_id=current_user.driver.id,
        status=RouteStatus.PLANNED
    ).order_by(Route.start_time).offset(1).limit(5).all()

    completed_routes = Route.query.filter_by(
        driver_id=current_user.driver.id,
        status=RouteStatus.COMPLETED
    ).order_by(Route.end_time.desc()).limit(5).all()

    # Get driver stats
    stats = _get_driver_stats(current_user.driver.id)

    log_action(ActionType.VIEW, "Viewed driver routes dashboard", db)

    return render_template(
        'routes/routes_dashboard.html',
        title='My Routes',
        active_route=active_route,
        next_route=next_route,
        upcoming_routes=upcoming_routes,
        completed_routes=completed_routes,
        stats=stats
    )


@driver.route('/unread-messages')
@login_required
@role_required('driver')
def unread_messages():
    """
    Show unread messages for driver
    """
    # Get unread messages count
    unread_count = Message.query.filter_by(
        recipient_id=current_user.id,
        is_read=False
    ).count()

    # If no unread messages, redirect to inbox
    if unread_count == 0:
        return redirect(url_for('messages.inbox'))

    # Get first unread message
    first_unread = Message.query.filter_by(
        recipient_id=current_user.id,
        is_read=False
    ).order_by(Message.sent_at).first()

    # Redirect to chat with sender
    return redirect(url_for('messages.chat', user_id=first_unread.sender_id))


@driver.route('/tasks')
@login_required
@role_required('driver')
def tasks():
    """
    Show tasks assigned to driver
    """
    # Get assigned tasks
    active_tasks = Task.query.filter_by(
        assignee_id=current_user.id,
        status=TaskStatus.IN_PROGRESS
    ).order_by(Task.deadline).all()

    new_tasks = Task.query.filter_by(
        assignee_id=current_user.id,
        status=TaskStatus.NEW
    ).order_by(Task.deadline).all()

    completed_tasks = Task.query.filter_by(
        assignee_id=current_user.id,
        status=TaskStatus.COMPLETED
    ).order_by(Task.updated_at.desc()).limit(5).all()

    # Get task stats
    stats = {
        'total': len(active_tasks) + len(new_tasks) + len(completed_tasks),
        'active': len(active_tasks),
        'new': len(new_tasks),
        'completed': len(completed_tasks),
        'overdue': sum(1 for t in active_tasks + new_tasks if t.deadline and t.deadline < datetime.utcnow())
    }

    log_action(ActionType.VIEW, "Viewed driver tasks", db)

    return render_template(
        'driver/tasks.html',
        title='My Tasks',
        active_tasks=active_tasks,
        new_tasks=new_tasks,
        completed_tasks=completed_tasks,
        stats=stats,
        now=datetime.utcnow()
    )


@driver.route('/profile')
@login_required
@role_required('driver')
def profile():
    """
    Show driver profile
    """
    # Get operator info
    operator = None
    if current_user.driver and current_user.driver.operator_id:
        operator_user = User.query.join(
            User.operator
        ).filter(
            User.operator.has(id=current_user.driver.operator_id)
        ).first()

        if operator_user:
            operator = {
                'id': operator_user.id,
                'name': f"{operator_user.first_name} {operator_user.last_name}",
                'email': operator_user.email,
                'phone': operator_user.phone
            }

    # Get driver stats
    stats = _get_driver_stats(current_user.driver.id)

    log_action(ActionType.VIEW, "Viewed driver profile", db)

    return render_template(
        'driver/profile.html',
        title='Driver Profile',
        operator=operator,
        stats=stats
    )


# Helper functions
def _get_driver_stats(driver_id):
    """
    Get statistics for a driver
    """
    # Get all routes
    routes = Route.query.filter_by(driver_id=driver_id).all()

    # Calculate stats
    total_routes = len(routes)
    completed_routes = sum(1 for r in routes if r.status == RouteStatus.COMPLETED)
    active_routes = sum(1 for r in routes if r.status == RouteStatus.IN_PROGRESS)
    planned_routes = sum(1 for r in routes if r.status == RouteStatus.PLANNED)

    # Calculate total distance
    total_distance = sum(r.distance or 0 for r in routes if r.status == RouteStatus.COMPLETED)

    # Calculate average completion time (in minutes)
    completion_times = []
    for route in routes:
        if route.status == RouteStatus.COMPLETED and route.actual_start_time and route.end_time:
            duration = (route.end_time - route.actual_start_time).total_seconds() / 60  # in minutes
            completion_times.append(duration)

    avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0

    # Get on-time delivery rate
    on_time_deliveries = 0
    total_planned_deliveries = 0

    for route in routes:
        if route.status == RouteStatus.COMPLETED and route.end_time:
            if route.start_time:  # Only consider routes with planned start time
                total_planned_deliveries += 1
                # Add some buffer (e.g., 30 minutes)
                buffer = 30  # minutes
                planned_end_time = route.start_time
                if route.estimated_time:
                    # Add estimated time to planned start
                    from datetime import timedelta
                    planned_end_time = route.start_time + timedelta(minutes=route.estimated_time + buffer)

                if route.end_time <= planned_end_time:
                    on_time_deliveries += 1

    on_time_rate = (on_time_deliveries / total_planned_deliveries * 100) if total_planned_deliveries > 0 else 0

    return {
        'total_routes': total_routes,
        'completed_routes': completed_routes,
        'active_routes': active_routes,
        'planned_routes': planned_routes,
        'total_distance': total_distance,
        'avg_completion_time': round(avg_completion_time, 1) if avg_completion_time else 0,
        'on_time_rate': round(on_time_rate, 1),
        'performance_score': min(round((completed_routes / total_routes * 100) if total_routes > 0 else 0, 1), 100)
    }