from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import or_, and_, desc, func, case
from wtforms import SelectField, StringField
from wtforms.validators import DataRequired

from app import db
from forms import MessageForm
from models import Message, User, UserRole, Task, Company, ActionType
from models import CompanyOwner, Manager, Operator, Driver
from utils import log_action

messages = Blueprint('messages', __name__, url_prefix='/messages')


@messages.route('/inbox')
@login_required
def inbox():
    """
    Show inbox messages
    """
    page = request.args.get('page', 1, type=int)
    search_term = request.args.get('search', '')

    # Build query for received messages
    query = Message.query.filter_by(recipient_id=current_user.id)

    # Apply search if provided
    if search_term:
        search = f"%{search_term}%"
        query = query.filter(Message.content.ilike(search))

    # Order by sent time (newest first)
    query = query.order_by(Message.sent_at.desc())

    # Paginate results
    messages_pagination = query.paginate(page=page, per_page=10)

    # Get unread message count for badge
    unread_count = Message.query.filter_by(recipient_id=current_user.id, is_read=False).count()

    # Get current datetime for relative time display
    now = datetime.utcnow()

    log_action(ActionType.VIEW, "Viewed inbox", db)

    return render_template(
        'messages/inbox.html',
        title='Inbox',
        messages=messages_pagination,
        unread_count=unread_count,
        search_term=search_term,
        now=now
    )


@messages.route('/sent')
@login_required
def sent():
    """
    Show sent messages
    """
    page = request.args.get('page', 1, type=int)
    search_term = request.args.get('search', '')

    # Build query for sent messages
    query = Message.query.filter_by(sender_id=current_user.id)

    # Apply search if provided
    if search_term:
        search = f"%{search_term}%"
        query = query.filter(Message.content.ilike(search))

    # Order by sent time (newest first)
    query = query.order_by(Message.sent_at.desc())

    # Paginate results
    messages_pagination = query.paginate(page=page, per_page=10)

    # Get unread message count for badge
    unread_count = Message.query.filter_by(recipient_id=current_user.id, is_read=False).count()

    # Get current datetime for relative time display
    now = datetime.utcnow()

    log_action(ActionType.VIEW, "Viewed sent messages", db)

    return render_template(
        'messages/sent.html',
        title='Sent Messages',
        messages=messages_pagination,
        unread_count=unread_count,
        search_term=search_term,
        now=now
    )


@messages.route('/compose', methods=['GET', 'POST'])
@login_required
def compose():
    """
    Compose a new message
    """

    # Create a new form instance with dynamic fields
    class DynamicMessageForm(MessageForm):
        pass

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

    # Get available recipients based on role
    available_recipients = []

    if current_user.role == UserRole.ADMIN:
        # Admin can message anyone
        available_recipients = User.query.filter(User.id != current_user.id).all()
    elif current_user.role == UserRole.COMPANY_OWNER and company_id:
        # Company owner can message managers, operators, and drivers in their company
        manager_users = User.query.join(Manager).filter(Manager.company_id == company_id).all()
        operator_users = User.query.join(Operator).filter(Operator.company_id == company_id).all()
        driver_users = User.query.join(Driver).filter(Driver.company_id == company_id).all()

        # Combine all users
        available_recipients = manager_users + operator_users + driver_users
        # Remove duplicates if any
        available_recipients = list(set(available_recipients))
        # Remove current user if in the list
        available_recipients = [u for u in available_recipients if u.id != current_user.id]

    elif current_user.role == UserRole.MANAGER and company_id:
        # Manager can message company owner, other managers, operators, and drivers in their company
        owner_users = User.query.join(CompanyOwner).filter(CompanyOwner.company_id == company_id).all()
        manager_users = User.query.join(Manager).filter(Manager.company_id == company_id).all()
        operator_users = User.query.join(Operator).filter(Operator.company_id == company_id).all()
        driver_users = User.query.join(Driver).filter(Driver.company_id == company_id).all()

        # Combine all users
        available_recipients = owner_users + manager_users + operator_users + driver_users
        # Remove duplicates if any
        available_recipients = list(set(available_recipients))
        # Remove current user if in the list
        available_recipients = [u for u in available_recipients if u.id != current_user.id]

    elif current_user.role == UserRole.OPERATOR and company_id:
        # Operator can message company owner, managers, other operators, and their drivers
        owner_users = User.query.join(CompanyOwner).filter(CompanyOwner.company_id == company_id).all()
        manager_users = User.query.join(Manager).filter(Manager.company_id == company_id).all()
        operator_users = User.query.join(Operator).filter(Operator.company_id == company_id).all()

        # Get driver IDs assigned to this operator
        driver_ids = [driver.id for driver in current_user.operator.drivers]
        driver_users = User.query.filter(User.id.in_(driver_ids)).all() if driver_ids else []

        # Combine all users
        available_recipients = owner_users + manager_users + operator_users + driver_users
        # Remove duplicates if any
        available_recipients = list(set(available_recipients))
        # Remove current user if in the list
        available_recipients = [u for u in available_recipients if u.id != current_user.id]

    elif current_user.role == UserRole.DRIVER and company_id:
        # Driver can message their operator, and company admins
        owner_users = User.query.join(CompanyOwner).filter(CompanyOwner.company_id == company_id).all()
        manager_users = User.query.join(Manager).filter(Manager.company_id == company_id).all()

        # Add operator if assigned
        operator_users = []
        if current_user.driver.operator_id:
            operator = User.query.filter(User.id == current_user.driver.operator_id).first()
            if operator:
                operator_users = [operator]

        # Combine all users
        available_recipients = owner_users + manager_users + operator_users
        # Remove duplicates if any
        available_recipients = list(set(available_recipients))
        # Remove current user if in the list
        available_recipients = [u for u in available_recipients if u.id != current_user.id]

    # Add recipient_id field to the form class
    if available_recipients:
        setattr(DynamicMessageForm, 'recipient_id',
                SelectField('Recipient', choices=[(r.id, f"{r.first_name} {r.last_name} ({r.role.value})") for r in
                                                  available_recipients],
                            coerce=int, validators=[DataRequired()]))
    else:
        setattr(DynamicMessageForm, 'recipient_id',
                SelectField('Recipient', choices=[], coerce=int, validators=[DataRequired()]))

    # Create form instance after adding fields
    form = DynamicMessageForm()

    # Add task ID field if in context of a task
    task_id = request.args.get('task_id', None, type=int)
    if task_id:
        task = Task.query.get_or_404(task_id)
        form.task_id.data = task_id

    # Get recent contacts for sidebar
    recent_contacts = []
    if company_id:
        # Get all users this user has messaged with, ordered by most recent
        message_partners_subquery = db.session.query(
            case(
                (Message.sender_id == current_user.id, Message.recipient_id),
                else_=Message.sender_id
            ).label('contact_id'),
            func.max(Message.sent_at).label('last_message_time')
        ).filter(
            or_(
                and_(Message.sender_id == current_user.id, Message.recipient_id != current_user.id),
                and_(Message.recipient_id == current_user.id, Message.sender_id != current_user.id)
            )
        ).group_by(
            case(
                (Message.sender_id == current_user.id, Message.recipient_id),
                else_=Message.sender_id
            )
        ).subquery()

        recent_message_partners = db.session.query(
            message_partners_subquery.c.contact_id,
            message_partners_subquery.c.last_message_time
        ).order_by(
            desc(message_partners_subquery.c.last_message_time)
        ).limit(5).all()

        for contact_id, last_time in recent_message_partners:
            contact = User.query.get(contact_id)
            if contact:
                recent_contacts.append({
                    'user': contact,
                    'last_message_time': last_time
                })

    # Process form submission
    if form.validate_on_submit():
        recipient_id = form.recipient_id.data
        content = form.content.data

        # Create and save message
        message = Message(
            content=content,
            sender_id=current_user.id,
            recipient_id=recipient_id,
            sent_at=datetime.utcnow(),
            is_read=False,
            task_id=form.task_id.data if hasattr(form, 'task_id') else None,
            company_id=company_id
        )

        try:
            db.session.add(message)
            db.session.commit()
            log_action(ActionType.CREATE, f"Sent message to user ID {recipient_id}", db)
            flash('Message sent successfully!', 'success')

            # Redirect to chat with recipient
            return redirect(url_for('messages.chat', user_id=recipient_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error sending message: {str(e)}', 'danger')

    # Get unread count for navbar
    unread_count = Message.query.filter_by(recipient_id=current_user.id, is_read=False).count()

    return render_template(
        'messages/compose.html',
        title='Compose Message',
        form=form,
        unread_count=unread_count,
        recent_contacts=recent_contacts
    )


@messages.route('/chat/<int:user_id>', methods=['GET', 'POST'])
@login_required
def chat(user_id):
    """
    Chat with a specific user
    """
    other_user = User.query.get_or_404(user_id)

    # Check if users can message each other
    if not _can_message_user(other_user):
        flash('You cannot message this user.', 'danger')
        return redirect(url_for('messages.inbox'))

    # Get chat history
    messages_query = Message.query.filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.recipient_id == user_id),
            and_(Message.sender_id == user_id, Message.recipient_id == current_user.id)
        )
    ).order_by(Message.sent_at.asc())

    messages_list = messages_query.all()

    # Create form for sending new message
    form = MessageForm()
    form.content.label = None  # Remove label in chat view

    # Add task field if appropriate
    # Get tasks that involve both users
    tasks = []
    task_id = request.args.get('task_id', None, type=int)

    # Check if this is a task-related conversation
    is_task_related = False
    task = None

    if task_id:
        task = Task.query.get(task_id)
        form.task_id.data = task_id
        is_task_related = True

    # Mark received messages as read
    unread_messages = [m for m in messages_list if m.recipient_id == current_user.id and not m.is_read]
    for message in unread_messages:
        message.is_read = True

    # Get contacts for sidebar
    contacts = _get_user_contacts()

    # Process new message form
    if form.validate_on_submit():
        content = form.content.data
        task_id = form.task_id.data if hasattr(form, 'task_id') else None

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

        # Create and save message
        message = Message(
            content=content,
            sender_id=current_user.id,
            recipient_id=user_id,
            sent_at=datetime.utcnow(),
            is_read=False,
            task_id=task_id,
            company_id=company_id
        )

        try:
            db.session.add(message)

            # Also update read status for unread messages
            if unread_messages:
                db.session.bulk_save_objects(unread_messages)

            db.session.commit()
            log_action(ActionType.CREATE, f"Sent message to user ID {user_id}", db)

            # Clear form
            form.content.data = ""

            # Add the new message to the list
            messages_list.append(message)

        except Exception as e:
            db.session.rollback()
            flash(f'Error sending message: {str(e)}', 'danger')

    # Get unread count for navbar
    unread_count = Message.query.filter_by(recipient_id=current_user.id, is_read=False).count()

    return render_template(
        'messages/chat.html',
        title=f'Chat with {other_user.first_name} {other_user.last_name}',
        other_user=other_user,
        messages=messages_list,
        form=form,
        unread_count=unread_count,
        contacts=contacts,
        is_task_related=is_task_related,
        task=task,
        tasks=tasks
    )


@messages.route('/clear-chat/<int:user_id>', methods=['POST'])
@login_required
def clear_chat(user_id):
    """
    Clear chat history with a user
    """
    other_user = User.query.get_or_404(user_id)

    # Check permissions - only admins and company owners can clear chats
    if current_user.role not in [UserRole.ADMIN, UserRole.COMPANY_OWNER]:
        flash('You do not have permission to clear chat history.', 'danger')
        return redirect(url_for('messages.chat', user_id=user_id))

    try:
        # Delete all messages between the two users
        Message.query.filter(
            or_(
                and_(Message.sender_id == current_user.id, Message.recipient_id == user_id),
                and_(Message.sender_id == user_id, Message.recipient_id == current_user.id)
            )
        ).delete(synchronize_session=False)

        db.session.commit()
        log_action(ActionType.DELETE, f"Cleared chat history with user ID {user_id}", db)
        flash('Chat history cleared successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error clearing chat history: {str(e)}', 'danger')

    return redirect(url_for('messages.chat', user_id=user_id))


@messages.route('/send_message/<int:user_id>', methods=['POST'])
@login_required
def send_message(user_id):
    """
    Send a message to a specific user
    """
    other_user = User.query.get_or_404(user_id)

    # Check if users can message each other
    # Simple validation instead of _can_message_user
    if current_user.role == UserRole.DRIVER and other_user.role == UserRole.DRIVER:
        flash('Drivers cannot message other drivers.', 'danger')
        return redirect(url_for('messages.inbox'))

    # Get form data
    content = request.form.get('content')
    task_id = request.form.get('task_id')

    # Validate content
    if not content or len(content.strip()) == 0:
        flash('Message cannot be empty.', 'danger')
        return redirect(url_for('messages.chat', user_id=user_id))

    # Convert task_id to int or None
    if task_id and task_id.isdigit():
        task_id = int(task_id)
    else:
        task_id = None

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

    try:
        # Create and save message
        message = Message(
            content=content,
            sender_id=current_user.id,
            recipient_id=user_id,
            sent_at=datetime.utcnow(),
            is_read=False,
            task_id=task_id,
            company_id=company_id
        )

        db.session.add(message)
        db.session.commit()
        log_action(ActionType.CREATE, f"Sent message to user ID {user_id}", db)

        # No flash message - users don't need confirmation for each sent message
    except Exception as e:
        db.session.rollback()
        flash(f'Error sending message: {str(e)}', 'danger')

    return redirect(url_for('messages.chat', user_id=user_id))


# Helper functions
def _can_message_user(other_user):
    """
    Check if current user can message another user
    """
    # Admin can message anyone
    if current_user.role == UserRole.ADMIN:
        return True

    # Get company IDs
    current_company_id = None
    other_company_id = None

    if current_user.role == UserRole.COMPANY_OWNER and current_user.company_owner:
        current_company_id = current_user.company_owner.company_id
    elif current_user.role == UserRole.MANAGER and current_user.manager:
        current_company_id = current_user.manager.company_id
    elif current_user.role == UserRole.OPERATOR and current_user.operator:
        current_company_id = current_user.operator.company_id
    elif current_user.role == UserRole.DRIVER and current_user.driver:
        current_company_id = current_user.driver.company_id

    if other_user.role == UserRole.COMPANY_OWNER and other_user.company_owner:
        other_company_id = other_user.company_owner.company_id
    elif other_user.role == UserRole.MANAGER and other_user.manager:
        other_company_id = other_user.manager.company_id
    elif other_user.role == UserRole.OPERATOR and other_user.operator:
        other_company_id = other_user.operator.company_id
    elif other_user.role == UserRole.DRIVER and other_user.driver:
        other_company_id = other_user.driver.company_id

    # Users must be in the same company
    if current_company_id is None or other_company_id is None or current_company_id != other_company_id:
        return False

    # Special case: Driver can only message their operator or managers
    if current_user.role == UserRole.DRIVER:
        if other_user.role == UserRole.DRIVER:
            return False  # Drivers can't message other drivers

        if other_user.role == UserRole.OPERATOR and current_user.driver.operator_id != other_user.id:
            return False  # Driver can only message their assigned operator

    return True


def _get_user_contacts():
    """
    Get all contacts for current user with unread message counts
    """
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

    contacts = []

    if not company_id and current_user.role != UserRole.ADMIN:
        return contacts

    # Get all distinct users with whom the current user has exchanged messages
    senders = db.session.query(Message.sender_id).filter(
        Message.recipient_id == current_user.id,
        Message.sender_id != current_user.id
    ).distinct().all()

    recipients = db.session.query(Message.recipient_id).filter(
        Message.sender_id == current_user.id,
        Message.recipient_id != current_user.id
    ).distinct().all()

    # Объединяем уникальные ID
    contact_ids = set([sender[0] for sender in senders] + [recipient[0] for recipient in recipients])

    # Get user objects for all contacts
    for contact_id in contact_ids:
        contact = User.query.get(contact_id)

        if not contact:
            continue

        # Check if this is a valid contact (same company, etc.)
        if not _can_message_user(contact):
            continue

        # Count unread messages from this contact
        unread_count = Message.query.filter_by(
            sender_id=contact_id,
            recipient_id=current_user.id,
            is_read=False
        ).count()

        # Get last message time
        last_message = Message.query.filter(
            or_(
                and_(Message.sender_id == current_user.id, Message.recipient_id == contact_id),
                and_(Message.sender_id == contact_id, Message.recipient_id == current_user.id)
            )
        ).order_by(Message.sent_at.desc()).first()

        last_message_time = last_message.sent_at if last_message else None

        # Get role name
        role_name = contact.role.value.replace('_', ' ').title()

        contacts.append({
            'user': contact,
            'unread_count': unread_count,
            'last_message_time': last_message_time,
            'role_name': role_name
        })

    # Sort by unread count (descending), then by last message time (descending)
    contacts.sort(key=lambda x: (-x['unread_count'], x['last_message_time'] or datetime.min), reverse=True)

    return contacts