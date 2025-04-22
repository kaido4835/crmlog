import logging
import functools
import time
import traceback
from flask import request, current_app, g


def log_function(func):
    """
    Simple decorator to log function execution time and errors

    Usage:
        @log_function
        def your_function():
            ...
    """

    @functools.wraps(func)
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

    user_id = g.get('user_id', 'anonymous')

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