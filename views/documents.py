from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from utils import log_action

from app import db
from models import Document, User, UserRole, Task, TaskStatus, Route, RouteStatus, ActionType
from forms import DocumentUploadForm, DocumentSearchForm
from utils import role_required, company_access_required, log_action, save_document, delete_file

documents = Blueprint('documents', __name__, url_prefix='/documents')


@documents.route('/')
@login_required
def list_documents():
    """
    List all documents with filtering options
    """
    page = request.args.get('page', 1, type=int)
    search_term = request.args.get('search', '')
    task_id = request.args.get('task_id', None, type=int)

    # Get company ID based on user role
    company_id = None
    if current_user.role == UserRole.COMPANY_OWNER and current_user.company_owner:
        company_id = current_user.company_owner.company_id
    elif current_user.role == UserRole.MANAGER and current_user.manager:
        company_id = current_user.manager.company_id
    elif current_user.role == UserRole.OPERATOR and current_user.operator:
        company_id = current_user.operator.company_id
    elif current_user.role == UserRole.DRIVER and current_user.driver:
        company_id = current_user.driver.company_id

    # For admins, they can filter by company
    if current_user.role == UserRole.ADMIN:
        company_id = request.args.get('company_id', None, type=int)

    # Build query
    doc_query = Document.query

    # Apply company filter
    if company_id:
        doc_query = doc_query.filter(Document.company_id == company_id)

    # Apply task filter
    if task_id:
        doc_query = doc_query.filter(Document.task_id == task_id)

    # Apply search filter
    if search_term:
        doc_query = doc_query.filter(Document.title.ilike(f'%{search_term}%'))

    # Order by upload time (newest first)
    doc_query = doc_query.order_by(Document.uploaded_at.desc())

    # Paginate results
    documents = doc_query.paginate(page=page, per_page=10)

    # Get search form
    search_form = DocumentSearchForm()

    log_action(ActionType.VIEW, "Viewed documents list", db)

    return render_template(
        'documents/list_documents.html',
        title='Documents',
        documents=documents,
        search_term=search_term,
        task_id=task_id,
        company_id=company_id,
        search_form=search_form
    )


@documents.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_document():
    """
    Upload a new document
    """
    form = DocumentUploadForm()

    # Get company ID based on user role
    company_id = None
    if current_user.role == UserRole.COMPANY_OWNER and current_user.company_owner:
        company_id = current_user.company_owner.company_id
    elif current_user.role == UserRole.MANAGER and current_user.manager:
        company_id = current_user.manager.company_id
    elif current_user.role == UserRole.OPERATOR and current_user.operator:
        company_id = current_user.operator.company_id
    elif current_user.role == UserRole.DRIVER and current_user.driver:
        company_id = current_user.driver.company_id

    # For admins, they can select a company
    if current_user.role == UserRole.ADMIN:
        # Get all companies for dropdown
        all_companies = Company.query.all()
        form.company_id.choices = [(c.id, c.name) for c in all_companies]
    else:
        # Non-admins can only upload to their company
        if not company_id:
            flash('You are not associated with a company.', 'danger')
            return redirect(url_for('main.index'))

        # Hide company field for non-admins
        del form.company_id

    # Get task ID from query parameter
    task_id = request.args.get('task_id', None, type=int)

    # If task_id provided, validate it
    if task_id:
        task = Task.query.get_or_404(task_id)

        # Check if user has access to this task
        if not company_id or task.company_id != company_id:
            flash('You do not have access to this task.', 'danger')
            return redirect(url_for('documents.list_documents'))

        # Pre-select task in form
        form.task_id.data = task_id

    # Get available tasks for dropdown
    if company_id:
        task_query = Task.query.filter_by(company_id=company_id)

        # For drivers, only show their tasks
        if current_user.role == UserRole.DRIVER:
            task_query = task_query.filter_by(assignee_id=current_user.id)

        tasks = task_query.all()

        # Update task choices
        form.task_id.choices = [(t.id, t.title) for t in tasks]
        form.task_id.choices.insert(0, (0, 'No task'))

    if form.validate_on_submit():
        try:
            # Get company ID (either from form or from user)
            doc_company_id = form.company_id.data if hasattr(form, 'company_id') else company_id

            # Get task ID (0 means no task)
            doc_task_id = form.task_id.data if form.task_id.data != 0 else None

            # If task ID provided, verify it
            if doc_task_id:
                task = Task.query.get_or_404(doc_task_id)

                # Check if user has access to this task
                if not doc_company_id or task.company_id != doc_company_id:
                    flash('You do not have access to this task.', 'danger')
                    return redirect(url_for('documents.upload_document'))

            # Save document
            file = form.document.data
            file_path, file_type, file_size = save_document(file, doc_task_id, doc_company_id)

            if not file_path:
                flash('Error saving document. Please check file type and size.', 'danger')
                return redirect(url_for('documents.upload_document'))

            # Create document record
            document = Document(
                title=form.title.data,
                file_path=file_path,
                file_type=file_type,
                size=file_size,
                uploader_id=current_user.id,
                task_id=doc_task_id,
                company_id=doc_company_id,
                uploaded_at=datetime.utcnow()
            )

            db.session.add(document)
            db.session.commit()

            log_action(ActionType.CREATE, f"Uploaded document: {document.title}", db)
            flash('Document uploaded successfully!', 'success')

            # Redirect to document list, with task filter if applicable
            if doc_task_id:
                return redirect(url_for('documents.list_documents', task_id=doc_task_id))
            else:
                return redirect(url_for('documents.list_documents'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error uploading document: {str(e)}', 'danger')

    return render_template(
        'documents/upload_document.html',
        title='Upload Document',
        form=form
    )


@documents.route('/<int:document_id>')
@login_required
def view_document(document_id):
    """
    View document details
    """
    document = Document.query.get_or_404(document_id)

    # Check if user has access to this document
    if not _can_access_document(document):
        flash('You do not have permission to access this document.', 'danger')
        return redirect(url_for('documents.list_documents'))

    log_action(ActionType.VIEW, f"Viewed document: {document.title}", db)

    return render_template(
        'documents/view_document.html',
        title=f'Document: {document.title}',
        document=document
    )


@documents.route('/<int:document_id>/download')
@login_required
def download_document(document_id):
    """
    Download a document
    """
    document = Document.query.get_or_404(document_id)

    # Check if user has access to this document
    if not _can_access_document(document):
        flash('You do not have permission to access this document.', 'danger')
        return redirect(url_for('documents.list_documents'))

    # Get the full path to the file
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], document.file_path.lstrip('uploads/'))

    if not os.path.exists(file_path):
        flash('Document file not found. Please contact an administrator.', 'danger')
        return redirect(url_for('documents.view_document', document_id=document_id))

    # Log the download
    log_action(ActionType.DOWNLOAD, f"Downloaded document: {document.title}", db)

    # Get filename from document title and file type
    filename = secure_filename(f"{document.title}.{document.file_type}")

    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename
    )


@documents.route('/<int:document_id>/delete', methods=['POST'])
@login_required
def delete_document(document_id):
    """
    Delete a document
    """
    document = Document.query.get_or_404(document_id)

    # Check if user has permission to delete this document
    if not _can_delete_document(document):
        flash('You do not have permission to delete this document.', 'danger')
        return redirect(url_for('documents.view_document', document_id=document_id))

    try:
        # Get the task ID for redirect after delete
        task_id = document.task_id

        # Delete the file from storage
        delete_file(document.file_path)

        # Delete the database record
        title = document.title
        db.session.delete(document)
        db.session.commit()

        log_action(ActionType.DELETE, f"Deleted document: {title}", db)
        flash(f'Document "{title}" deleted successfully!', 'success')

        # Redirect to the task if this was a task document
        if task_id:
            return redirect(url_for('tasks.view_task', task_id=task_id))
        else:
            return redirect(url_for('documents.list_documents'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting document: {str(e)}', 'danger')
        return redirect(url_for('documents.view_document', document_id=document_id))


@documents.route('/<int:document_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_document(document_id):
    """
    Edit document metadata
    """
    document = Document.query.get_or_404(document_id)

    # Check if user has permission to edit this document
    if not _can_edit_document(document):
        flash('You do not have permission to edit this document.', 'danger')
        return redirect(url_for('documents.view_document', document_id=document_id))

    # Create form
    form = DocumentUploadForm()

    # Remove document upload field - we're just editing metadata
    delattr(form, 'document')

    # Get company ID based on user role
    company_id = None
    if current_user.role == UserRole.COMPANY_OWNER and current_user.company_owner:
        company_id = current_user.company_owner.company_id
    elif current_user.role == UserRole.MANAGER and current_user.manager:
        company_id = current_user.manager.company_id
    elif current_user.role == UserRole.OPERATOR and current_user.operator:
        company_id = current_user.operator.company_id
    elif current_user.role == UserRole.DRIVER and current_user.driver:
        company_id = current_user.driver.company_id

    # For admins, they can select a company
    if current_user.role == UserRole.ADMIN:
        # Get all companies for dropdown
        all_companies = Company.query.all()
        form.company_id.choices = [(c.id, c.name) for c in all_companies]
    else:
        # Non-admins can only assign to their company
        if not company_id:
            flash('You are not associated with a company.', 'danger')
            return redirect(url_for('documents.view_document', document_id=document_id))

        # Hide company field for non-admins
        del form.company_id

    # Get available tasks for dropdown
    if company_id:
        task_query = Task.query.filter_by(company_id=company_id)

        # For drivers, only show their tasks
        if current_user.role == UserRole.DRIVER:
            task_query = task_query.filter_by(assignee_id=current_user.id)

        tasks = task_query.all()

        # Update task choices
        form.task_id.choices = [(t.id, t.title) for t in tasks]
        form.task_id.choices.insert(0, (0, 'No task'))

    # For GET requests, fill form with current data
    if request.method == 'GET':
        form.title.data = document.title
        form.task_id.data = document.task_id if document.task_id else 0
        if hasattr(form, 'company_id'):
            form.company_id.data = document.company_id

    if form.validate_on_submit():
        try:
            # Update document metadata
            document.title = form.title.data

            # Update task if changed
            new_task_id = form.task_id.data if form.task_id.data != 0 else None
            if new_task_id != document.task_id:
                document.task_id = new_task_id

            # Update company if allowed and changed
            if hasattr(form, 'company_id') and form.company_id.data != document.company_id:
                document.company_id = form.company_id.data

            db.session.commit()

            log_action(ActionType.UPDATE, f"Updated document: {document.title}", db)
            flash('Document updated successfully!', 'success')

            return redirect(url_for('documents.view_document', document_id=document_id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating document: {str(e)}', 'danger')

    return render_template(
        'documents/edit_document.html',
        title=f'Edit Document: {document.title}',
        form=form,
        document=document
    )


@documents.route('/by-task/<int:task_id>')
@login_required
def task_documents(task_id):
    """
    Show documents for a specific task
    """
    task = Task.query.get_or_404(task_id)

    # Check if user can access this task
    company_id = None
    if current_user.role == UserRole.COMPANY_OWNER and current_user.company_owner:
        company_id = current_user.company_owner.company_id
    elif current_user.role == UserRole.MANAGER and current_user.manager:
        company_id = current_user.manager.company_id
    elif current_user.role == UserRole.OPERATOR and current_user.operator:
        company_id = current_user.operator.company_id
    elif current_user.role == UserRole.DRIVER and current_user.driver:
        company_id = current_user.driver.company_id

    # Check if user has access to this task's company
    if current_user.role != UserRole.ADMIN and (not company_id or task.company_id != company_id):
        # Special case: driver can access their assigned tasks
        if not (current_user.role == UserRole.DRIVER and task.assignee_id == current_user.id):
            flash('You do not have access to this task.', 'danger')
            return redirect(url_for('documents.list_documents'))

    # Get task documents
    page = request.args.get('page', 1, type=int)
    documents = Document.query.filter_by(task_id=task_id).order_by(Document.uploaded_at.desc()).paginate(page=page,
                                                                                                         per_page=10)

    log_action(ActionType.VIEW, f"Viewed documents for task: {task.title}", db)

    return render_template(
        'documents/task_documents.html',
        title=f'Documents for Task: {task.title}',
        documents=documents,
        task=task
    )


@documents.route('/search', methods=['GET', 'POST'])
@login_required
def search_documents():
    """
    Advanced search for documents
    """
    form = DocumentSearchForm()

    # Get company ID based on user role
    company_id = None
    if current_user.role == UserRole.COMPANY_OWNER and current_user.company_owner:
        company_id = current_user.company_owner.company_id
    elif current_user.role == UserRole.MANAGER and current_user.manager:
        company_id = current_user.manager.company_id
    elif current_user.role == UserRole.OPERATOR and current_user.operator:
        company_id = current_user.operator.company_id
    elif current_user.role == UserRole.DRIVER and current_user.driver:
        company_id = current_user.driver.company_id

    # For admins, they can filter by company
    if current_user.role == UserRole.ADMIN:
        # Get all companies for dropdown
        all_companies = Company.query.all()
        form.company_id.choices = [(c.id, c.name) for c in all_companies]
        form.company_id.choices.insert(0, (0, 'All Companies'))
    else:
        # Non-admins can only search in their company
        del form.company_id

    # Get available file types for dropdown
    file_types = db.session.query(Document.file_type).distinct().all()
    form.file_type.choices = [(ft[0], ft[0].upper()) for ft in file_types]
    form.file_type.choices.insert(0, ('', 'All Types'))

    # Initialize results
    results = []
    searched = False

    if form.validate_on_submit() or request.args.get('search'):
        searched = True

        # Build search query
        search_query = Document.query

        # Apply company filter
        if hasattr(form, 'company_id') and form.company_id.data != 0:
            search_query = search_query.filter(Document.company_id == form.company_id.data)
        elif not hasattr(form, 'company_id') and company_id:
            search_query = search_query.filter(Document.company_id == company_id)

        # Apply title filter
        if form.title.data:
            search_query = search_query.filter(Document.title.ilike(f'%{form.title.data}%'))

        # Apply file type filter
        if form.file_type.data:
            search_query = search_query.filter(Document.file_type == form.file_type.data)

        # Apply date range filters
        if form.date_from.data:
            search_query = search_query.filter(Document.uploaded_at >= form.date_from.data)

        if form.date_to.data:
            # Set time to end of day
            end_date = form.date_to.data.replace(hour=23, minute=59, second=59)
            search_query = search_query.filter(Document.uploaded_at <= end_date)

        # Apply uploader filter if admin/manager/owner
        if form.uploader_id.data and form.uploader_id.data != 0:
            search_query = search_query.filter(Document.uploader_id == form.uploader_id.data)

        # Order by upload time (newest first)
        search_query = search_query.order_by(Document.uploaded_at.desc())

        # Execute query
        results = search_query.all()

        log_action(ActionType.VIEW, "Performed document search", db)

    # Get uploaders list for dropdown (for admins/managers/owners)
    uploaders = []
    if current_user.role in [UserRole.ADMIN, UserRole.COMPANY_OWNER, UserRole.MANAGER] and company_id:
        uploader_query = db.session.query(
            Document.uploader_id, User.first_name, User.last_name
        ).join(
            User, Document.uploader_id == User.id
        )

        if company_id:
            uploader_query = uploader_query.filter(Document.company_id == company_id)

        uploaders = uploader_query.distinct().all()

        form.uploader_id.choices = [(u[0], f"{u[1]} {u[2]}") for u in uploaders]
        form.uploader_id.choices.insert(0, (0, 'All Uploaders'))

    return render_template(
        'documents/search_documents.html',
        title='Document Search',
        form=form,
        results=results,
        searched=searched
    )


# Helper functions
def _can_access_document(document):
    """
    Check if current user can access a document
    """
    # Admin can access any document
    if current_user.role == UserRole.ADMIN:
        return True

    # Get company ID based on user role
    company_id = None
    if current_user.role == UserRole.COMPANY_OWNER and current_user.company_owner:
        company_id = current_user.company_owner.company_id
    elif current_user.role == UserRole.MANAGER and current_user.manager:
        company_id = current_user.manager.company_id
    elif current_user.role == UserRole.OPERATOR and current_user.operator:
        company_id = current_user.operator.company_id
    elif current_user.role == UserRole.DRIVER and current_user.driver:
        company_id = current_user.driver.company_id

    # Must be in same company
    if document.company_id != company_id:
        # Special case: driver can access documents for their assigned tasks
        if current_user.role == UserRole.DRIVER and document.task_id:
            task = Task.query.get(document.task_id)
            if task and task.assignee_id == current_user.id:
                return True
        return False

    return True


def _can_edit_document(document):
    """
    Check if current user can edit a document
    """
    # Admin can edit any document
    if current_user.role == UserRole.ADMIN:
        return True

    # Document uploader can edit
    if document.uploader_id == current_user.id:
        return True

    # Company owner and manager can edit company documents
    if current_user.role == UserRole.COMPANY_OWNER and current_user.company_owner and document.company_id == current_user.company_owner.company_id:
        return True

    if current_user.role == UserRole.MANAGER and current_user.manager and document.company_id == current_user.manager.company_id:
        return True

    return False


def _can_delete_document(document):
    """
    Check if current user can delete a document
    """
    # Admin can delete any document
    if current_user.role == UserRole.ADMIN:
        return True

    # Document uploader can delete
    if document.uploader_id == current_user.id:
        return True

    # Company owner and manager can delete company documents
    if current_user.role == UserRole.COMPANY_OWNER and current_user.company_owner and document.company_id == current_user.company_owner.company_id:
        return True

    if current_user.role == UserRole.MANAGER and current_user.manager and document.company_id == current_user.manager.company_id:
        return True

    return False