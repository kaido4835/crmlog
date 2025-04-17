import os
import uuid
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
        Relative path to saved file
    """
    if file:
        filename = secure_filename(file.filename)
        # Generate unique filename to prevent overwriting
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        upload_folder = current_app.config['UPLOAD_FOLDER']

        # Create upload folder if it doesn't exist
        os.makedirs(os.path.join(upload_folder, 'profile_images'), exist_ok=True)

        file_path = os.path.join(upload_folder, 'profile_images', unique_filename)
        file.save(file_path)

        # Return relative path to be stored in database
        return f'uploads/profile_images/{unique_filename}'

    return None


def admin_required(f):
    """
    Decorator that checks if the current user is an admin
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role.value != 'admin':
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
            if not current_user.is_authenticated or current_user.role.value not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def log_action(action_type, description, db_session):
    """
    Log user action to database

    Args:
        action_type: Type of action (from ActionType enum)
        description: Description of the action
        db_session: SQLAlchemy session
    """
    if current_user.is_authenticated:
        log_entry = Log(
            action_type=action_type,
            description=description,
            user_id=current_user.id,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db_session.add(log_entry)
        db_session.commit()


def save_document(file, task_id):
    """
    Save document file to upload folder with unique filename

    Args:
        file: File object from form
        task_id: ID of the task the document belongs to

    Returns:
        Tuple of (file_path, file_type, file_size)
    """
    if file:
        filename = secure_filename(file.filename)
        # Generate unique filename to prevent overwriting
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        upload_folder = current_app.config['UPLOAD_FOLDER']

        # Create upload folder with task-specific subfolder
        document_folder = os.path.join(upload_folder, 'documents', str(task_id))
        os.makedirs(document_folder, exist_ok=True)

        file_path = os.path.join(document_folder, unique_filename)
        file.save(file_path)

        # Get file extension as type
        file_type = os.path.splitext(filename)[1].lstrip('.')
        # Get file size in bytes
        file_size = os.path.getsize(file_path)

        # Return relative path to be stored in database
        return (f'uploads/documents/{task_id}/{unique_filename}', file_type, file_size)

    return None, None, None