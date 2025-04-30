import os
import re
import uuid
import shutil
from functools import wraps
from urllib.parse import urlparse, parse_qs

import requests
from flask import abort, flash, redirect, url_for, request, current_app, g
from flask_login import current_user
from werkzeug.utils import secure_filename
import logging
import time
import traceback

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

        if current_user.role.value != 'ADMIN':
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

            # Convert required roles to uppercase for comparison if they're lowercase in code
            upper_roles = [role.upper() if isinstance(role, str) else role for role in roles]

            if current_user.role.value not in upper_roles:
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
        db_session: SQLAlchemy session or db instance
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
            # Handle both cases - when db instance or db.session is passed
            if hasattr(db_session, 'session'):
                db_session.session.add(log_entry)
                db_session.session.commit()
            else:
                db_session.add(log_entry)
                db_session.commit()
        except Exception as e:
            # Handle both cases for rollback as well
            if hasattr(db_session, 'session'):
                db_session.session.rollback()
            else:
                db_session.rollback()
            current_app.logger.error(f"Error logging action: {str(e)}")


def save_document(file, task_id, company_id):
    """
    Save document file to upload folder with unique filename

    Args:
        file: File object from form
        task_id: ID of the task the document belongs to (can be None)
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

        # Make sure main upload folder exists
        os.makedirs(upload_folder, exist_ok=True)

        # Create appropriate folder path based on whether task_id is provided
        if task_id:
            # Create folder for task document
            document_folder = os.path.join(upload_folder, 'documents', str(company_id), str(task_id))
        else:
            # Create folder for general company document
            document_folder = os.path.join(upload_folder, 'documents', str(company_id), 'general')

        os.makedirs(document_folder, exist_ok=True)

        # Save the file
        file_path = os.path.join(document_folder, unique_filename)
        file.save(file_path)

        # Get file extension as type (without the dot)
        file_type = file_ext.lstrip('.') if file_ext else 'unknown'
        # Get file size in bytes
        file_size = os.path.getsize(file_path)

        # Construct relative path for database storage
        if task_id:
            relative_path = f"uploads/documents/{company_id}/{task_id}/{unique_filename}"
        else:
            relative_path = f"uploads/documents/{company_id}/general/{unique_filename}"

        # Log file information
        current_app.logger.info(f"Document saved successfully at: {file_path}")
        current_app.logger.info(f"Relative path for database: {relative_path}")
        current_app.logger.info(f"File type: {file_type}, File size: {file_size}")

        return (relative_path, file_type, file_size)
    except Exception as e:
        current_app.logger.error(f"Error saving document: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
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


# Added from simple_log_utils.py
def log_function(func):
    """
    Simple decorator to log function execution time and errors

    Usage:
        @log_function
        def your_function():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = current_app.logger
        func_name = func.__name__
        module_name = func.__module__

        logger.info(f"Executing: {module_name}.{func_name}")
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"Completed: {module_name}.{func_name} in {execution_time:.4f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error in {module_name}.{func_name} after {execution_time:.4f}s: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    return wrapper


def log_db_operation(operation_type, entity_name, entity_id=None, details=None):
    """
    Log database operations for auditing

    Args:
        operation_type: Type of operation (e.g., 'create', 'update', 'delete')
        entity_name: Name of the entity (e.g., 'User', 'Task', 'Document')
        entity_id: ID of the entity (optional)
        details: Additional details (optional)
    """
    logger = current_app.logger

    message = f"DB {operation_type.upper()}: {entity_name}"
    if entity_id:
        message += f" ID={entity_id}"
    if details:
        message += f" - {details}"

    logger.info(message)


def log_request():
    """Log basic information about the current request"""
    logger = current_app.logger

    # Only run within a request context
    if not hasattr(request, 'remote_addr'):
        return

    user_id = getattr(g, 'user_id', 'anonymous') if 'g' in globals() else 'anonymous'

    message = f"Request: {request.method} {request.path} - User: {user_id} - IP: {request.remote_addr}"
    logger.info(message)


def log_error(error, context=None):
    """
    Log an error with optional context

    Args:
        error: Exception or error message
        context: Additional context information (optional)
    """
    logger = current_app.logger

    if isinstance(error, Exception):
        error_message = f"{error.__class__.__name__}: {str(error)}"
        logger.error(error_message)
        logger.error(traceback.format_exc())
    else:
        error_message = str(error)
        logger.error(error_message)

    if context:
        logger.error(f"Error context: {context}")


def extract_coordinates_from_maps_url(url):
    """
    Extract latitude and longitude from a Google Maps URL.

    Args:
        url (str): Google Maps URL

    Returns:
        dict: Dictionary with lat and lng or error message
    """
    # Regular expressions for different Google Maps URL formats
    coords_patterns = [
        # Pattern 1: https://www.google.com/maps?q=51.507,-0.127
        re.compile(r'google\.com/maps\?q=(-?\d+\.\d+),(-?\d+\.\d+)'),

        # Pattern 2: https://www.google.com/maps/@51.507,-0.127,15z
        re.compile(r'google\.com/maps/@(-?\d+\.\d+),(-?\d+\.\d+)'),

        # Pattern 3: https://www.google.com/maps/place/.../data=!3m1!...!4m5!...!8m2!3d51.507!4d-0.127
        re.compile(r'google\.com/maps/.*!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)'),

        # Pattern 4: https://www.google.com/maps/place/.../ll=51.507,-0.127/data=...
        re.compile(r'google\.com/maps/.*ll=(-?\d+\.\d+),(-?\d+\.\d+)'),

        # Pattern 5: https://goo.gl/maps/XXXX -> Need to follow redirect

        # Pattern 6: Coordinates in the fragment part of URL: #52.22967,21.01223
        re.compile(r'#(-?\d+\.\d+),(-?\d+\.\d+)'),
    ]

    try:
        # Validate URL
        if not url or not isinstance(url, str):
            return {'success': False, 'error': 'Invalid URL format'}

        # Handle shortened URLs by following redirects
        if 'goo.gl' in url or 'maps.app.goo.gl' in url:
            try:
                response = requests.head(url, allow_redirects=True, timeout=5)
                url = response.url
            except Exception as e:
                return {'success': False, 'error': f'Error expanding shortened URL: {str(e)}'}

        # Try all patterns to extract coordinates
        for pattern in coords_patterns:
            match = pattern.search(url)
            if match:
                lat = float(match.group(1))
                lng = float(match.group(2))

                # Validate reasonable coordinates
                if -90 <= lat <= 90 and -180 <= lng <= 180:
                    return {
                        'success': True,
                        'lat': lat,
                        'lng': lng
                    }

        # Check for 'place' parameter which we can geocode
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        path = parsed_url.path

        # Extract place from path (common in newer Google Maps URLs)
        place_match = re.search(r'/place/([^/]+)', path)
        if place_match:
            place = place_match.group(1)
            return {
                'success': False,
                'error': 'Coordinates not found in URL',
                'place': place  # Return place which can be geocoded by the client
            }

        # If we got here, we couldn't extract coordinates
        return {'success': False, 'error': 'Coordinates not found in URL'}

    except Exception as e:
        return {'success': False, 'error': f'Error extracting coordinates: {str(e)}'}