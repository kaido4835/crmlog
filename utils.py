import os
import uuid
import shutil
from functools import wraps
from flask import abort, flash, redirect, url_for, request, current_app
from flask_login import current_user
from werkzeug.utils import secure_filename

from models import ActionType, Log


def save_profile_image(file):
    """
    Save profile image to upload folder with unique filename

    Args:
        file: File object from form

    Returns:
        Relative path to saved file or None if file is invalid
    """
    if not file:
        return None

    try:
        filename = secure_filename(file.filename)
        # Get file extension for validation
        _, file_ext = os.path.splitext(filename)
        file_ext = file_ext.lower()

        # Validate file extension
        allowed_extensions = ['.jpg', '.jpeg', '.png']
        if file_ext not in allowed_extensions:
            raise ValueError(f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}")

        # Generate unique filename to prevent overwriting
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        upload_folder = current_app.config['UPLOAD_FOLDER']

        # Create upload folder if it doesn't exist
        profile_images_dir = os.path.join(upload_folder, 'profile_images')
        os.makedirs(profile_images_dir, exist_ok=True)

        file_path = os.path.join(profile_images_dir, unique_filename)
        file.save(file_path)

        # Return relative path to be stored in database
        return f'uploads/profile_images/{unique_filename}'
    except Exception as e:
        current_app.logger.error(f"Error saving profile image: {str(e)}")
        return None


def admin_required(f):
    """
    Decorator that checks if the current user is an admin
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in first.', 'warning')
            return redirect(url_for('auth.login', next=request.url))

        if not current_user.is_active:
            flash('Your account is inactive.', 'danger')
            return redirect(url_for('main.index'))

        if current_user.role.value != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))

        return f(*args, **kwargs)

    return decorated_function


def role_required(roles):
    """
    Decorator that checks if the current user has one of the required roles

    Args:
        roles: A list of role values or a single role value
    """
    if isinstance(roles, str):
        roles = [roles]

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in first.', 'warning')
                return redirect(url_for('auth.login', next=request.url))

            if not current_user.is_active:
                flash('Your account is inactive.', 'danger')
                return redirect(url_for('main.index'))

            if current_user.role.value not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('main.index'))

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def company_access_required(f):
    """
    Decorator that checks if the current user has access to a specific company
    Used for views that receive company_id as a parameter
    """

    @wraps(f)
    def decorated_function(company_id, *args, **kwargs):
        # Admin has access to all companies
        if current_user.role.value == 'admin':
            return f(company_id, *args, **kwargs)

        # Company owner, manager, operator, driver must be associated with the company
        if current_user.role.value == 'company_owner' and current_user.company_owner.company_id != company_id:
            flash('You do not have access to this company.', 'danger')
            return redirect(url_for('main.index'))

        if current_user.role.value == 'manager' and current_user.manager.company_id != company_id:
            flash('You do not have access to this company.', 'danger')
            return redirect(url_for('main.index'))

        if current_user.role.value == 'operator' and current_user.operator.company_id != company_id:
            flash('You do not have access to this company.', 'danger')
            return redirect(url_for('main.index'))

        if current_user.role.value == 'driver' and current_user.driver.company_id != company_id:
            flash('You do not have access to this company.', 'danger')
            return redirect(url_for('main.index'))

        return f(company_id, *args, **kwargs)

    return decorated_function


def log_action(action_type, description, db_session):
    """
    Log user action to database

    Args:
        action_type: Type of action (from ActionType enum)
        description: Description of the action
        db_session: SQLAlchemy session
    """
    if current_user.is_authenticated:
        company_id = None

        # Get the user's company ID based on their role
        if current_user.role.value == 'company_owner' and current_user.company_owner:
            company_id = current_user.company_owner.company_id
        elif current_user.role.value == 'manager' and current_user.manager:
            company_id = current_user.manager.company_id
        elif current_user.role.value == 'operator' and current_user.operator:
            company_id = current_user.operator.company_id
        elif current_user.role.value == 'driver' and current_user.driver:
            company_id = current_user.driver.company_id

        log_entry = Log(
            action_type=action_type,
            description=description,
            user_id=current_user.id,
            company_id=company_id,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )

        try:
            # Исправлено с db_session.session.add(log_entry) на db_session.add(log_entry)
            db_session.add(log_entry)
            # Исправлено с db_session.session.commit() на db_session.commit()
            db_session.commit()
        except Exception as e:
            # Исправлено с db_session.session.rollback() на db_session.rollback()
            db_session.rollback()
            current_app.logger.error(f"Error logging action: {str(e)}")


def save_document(file, task_id, company_id):
    """
    Save document file to upload folder with unique filename

    Args:
        file: File object from form
        task_id: ID of the task the document belongs to
        company_id: ID of the company the document belongs to

    Returns:
        Tuple of (file_path, file_type, file_size) or (None, None, None) if file is invalid
    """
    if not file:
        return None, None, None

    try:
        filename = secure_filename(file.filename)

        # Get file extension
        _, file_ext = os.path.splitext(filename)
        file_ext = file_ext.lower()

        # Generate unique filename to prevent overwriting
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        upload_folder = current_app.config['UPLOAD_FOLDER']

        # Create upload folder with company and task-specific subfolder
        document_folder = os.path.join(upload_folder, 'documents', str(company_id), str(task_id))
        os.makedirs(document_folder, exist_ok=True)

        file_path = os.path.join(document_folder, unique_filename)
        file.save(file_path)

        # Get file extension as type (without the dot)
        file_type = file_ext.lstrip('.') if file_ext else 'unknown'
        # Get file size in bytes
        file_size = os.path.getsize(file_path)

        # Return relative path to be stored in database
        return (f'uploads/documents/{company_id}/{task_id}/{unique_filename}', file_type, file_size)
    except Exception as e:
        current_app.logger.error(f"Error saving document: {str(e)}")
        return None, None, None


def delete_file(file_path):
    """
    Delete a file from the file system

    Args:
        file_path: Relative path to the file

    Returns:
        True if the file was deleted successfully, False otherwise
    """
    if not file_path:
        return False

    try:
        abs_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_path.lstrip('uploads/'))
        if os.path.exists(abs_path):
            os.remove(abs_path)
            return True
        return False
    except Exception as e:
        current_app.logger.error(f"Error deleting file: {str(e)}")
        return False


def create_pagination_dict(pagination, endpoint, **kwargs):
    """
    Create a dictionary with pagination information

    Args:
        pagination: SQLAlchemy pagination object
        endpoint: Name of the endpoint for generating URLs
        **kwargs: Additional URL parameters

    Returns:
        Dictionary with pagination information
    """
    return {
        'items': pagination.items,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'total': pagination.total,
        'pages': pagination.pages,
        'has_prev': pagination.has_prev,
        'has_next': pagination.has_next,
        'prev_url': url_for(endpoint, page=pagination.prev_num, **kwargs) if pagination.has_prev else None,
        'next_url': url_for(endpoint, page=pagination.next_num, **kwargs) if pagination.has_next else None
    }