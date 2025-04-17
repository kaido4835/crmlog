from datetime import datetime
from flask import current_app
import os
from werkzeug.security import generate_password_hash

from models import (
    User, UserRole, Admin, CompanyOwner, Manager, Operator, Driver,
    Company, Task, TaskStatus, Route, RouteStatus, Document, Log, ActionType
)
from utils import log_action, save_profile_image, save_document


class UserService:
    @staticmethod
    def create_user(form, db_session, role=None, save_changes=True):
        """
        Create a new user from form data

        Args:
            form: Form containing user data
            db_session: SQLAlchemy session
            role: Override role from form
            save_changes: Whether to commit changes to database

        Returns:
            Created user object
        """
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            role=UserRole(role if role else form.role.data),
            is_active=form.is_active.data if hasattr(form, 'is_active') else True,
        )
        user.set_password(form.password.data)

        # Handle profile image if present
        if hasattr(form, 'profile_image') and form.profile_image.data:
            user.profile_image = save_profile_image(form.profile_image.data)

        db_session.add(user)
        if save_changes:
            db_session.commit()
            log_action(ActionType.CREATE, f"Created user {user.username}", db_session)

        return user

    @staticmethod
    def update_user(user, form, db_session):
        """
        Update existing user from form data

        Args:
            user: User object to update
            form: Form containing updated user data
            db_session: SQLAlchemy session

        Returns:
            Updated user object
        """
        user.username = form.username.data
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.phone = form.phone.data

        if hasattr(form, 'role'):
            old_role = user.role
            new_role = UserRole(form.role.data)

            if old_role != new_role:
                # Role has changed, we need to handle role-specific models
                UserService._handle_role_change(user, old_role, new_role, db_session)

        if hasattr(form, 'is_active'):
            user.is_active = form.is_active.data

        # Handle profile image if present
        if hasattr(form, 'profile_image') and form.profile_image.data:
            # Delete old profile image if exists
            if user.profile_image:
                old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], user.profile_image)
                if os.path.exists(old_path):
                    os.remove(old_path)

            user.profile_image = save_profile_image(form.profile_image.data)

        db_session.commit()
        log_action(ActionType.UPDATE, f"Updated user {user.username}", db_session)

        return user

    @staticmethod
    def _handle_role_change(user, old_role, new_role, db_session):
        """
        Handle changes when user role is updated

        Args:
            user: User object being updated
            old_role: Previous UserRole
            new_role: New UserRole
            db_session: SQLAlchemy session
        """
        # Remove previous role model
        if old_role == UserRole.ADMIN and user.admin:
            db_session.delete(user.admin)
        elif old_role == UserRole.COMPANY_OWNER and user.company_owner:
            db_session.delete(user.company_owner)
        elif old_role == UserRole.MANAGER and user.manager:
            db_session.delete(user.manager)
        elif old_role == UserRole.OPERATOR and user.operator:
            db_session.delete(user.operator)
        elif old_role == UserRole.DRIVER and user.driver:
            db_session.delete(user.driver)

        # Create new role model
        if new_role == UserRole.ADMIN:
            admin = Admin(id=user.id, admin_level=1)
            db_session.add(admin)
        elif new_role == UserRole.COMPANY_OWNER:
            # Cannot assign company owner without a company
            company_owner = CompanyOwner(id=user.id)
            db_session.add(company_owner)
        elif new_role == UserRole.MANAGER:
            # Cannot assign manager without a company
            manager = Manager(id=user.id)
            db_session.add(manager)
        elif new_role == UserRole.OPERATOR:
            # Cannot assign operator without a manager
            operator = Operator(id=user.id)
            db_session.add(operator)
        elif new_role == UserRole.DRIVER:
            # Cannot assign driver without an operator
            driver = Driver(id=user.id, license_number="", vehicle_info="")
            db_session.add(driver)

        # Update user role
        user.role = new_role

    @staticmethod
    def change_password(user, new_password, db_session):
        """
        Change user password

        Args:
            user: User object
            new_password: New password (plain text)
            db_session: SQLAlchemy session
        """
        user.password_hash = generate_password_hash(new_password)
        db_session.commit()
        log_action(ActionType.UPDATE, "Changed password", db_session)

    @staticmethod
    def create_admin(form, db_session):
        """
        Create a new admin user

        Args:
            form: Form containing user and admin data
            db_session: SQLAlchemy session

        Returns:
            Created user object
        """
        user = UserService.create_user(form, db_session, role=UserRole.ADMIN.value, save_changes=False)

        admin = Admin(id=user.id, admin_level=form.admin_level.data)
        db_session.add(admin)

        db_session.commit()
        log_action(ActionType.CREATE, f"Created admin {user.username}", db_session)

        return user

    @staticmethod
    def create_company_owner(form, db_session):
        """
        Create a new company owner user

        Args:
            form: Form containing user and company owner data
            db_session: SQLAlchemy session

        Returns:
            Created user object
        """
        user = UserService.create_user(form, db_session, role=UserRole.COMPANY_OWNER.value, save_changes=False)

        company_id = None

        # Handle company creation or selection
        if form.create_new_company.data:
            # Create new company
            company = Company(
                name=form.company_name.data,
                legal_name=form.company_legal_name.data,
                tax_id=form.company_tax_id.data,
                address=form.company_address.data,
                phone=form.company_phone.data,
                email=form.company_email.data,
                website=form.company_website.data
            )
            db_session.add(company)
            db_session.flush()  # Get company ID
            company_id = company.id
        else:
            # Use existing company
            company_id = form.company_id.data

        # Create company owner relationship
        company_owner = CompanyOwner(id=user.id, company_id=company_id)
        db_session.add(company_owner)

        db_session.commit()
        log_action(ActionType.CREATE, f"Created company owner {user.username}", db_session)

        return user


class CompanyService:
    @staticmethod
    def create_company(form, db_session):
        """
        Create a new company from form data

        Args:
            form: Form containing company data
            db_session: SQLAlchemy session

        Returns:
            Created company object
        """
        company = Company(
            name=form.name.data,
            legal_name=form.legal_name.data,
            tax_id=form.tax_id.data,
            address=form.address.data,
            phone=form.phone.data,
            email=form.email.data,
            website=form.website.data
        )

        db_session.add(company)
        db_session.commit()
        log_action(ActionType.CREATE, f"Created company {company.name}", db_session)

        return company

    @staticmethod
    def update_company(company, form, db_session):
        """
        Update existing company from form data

        Args:
            company: Company object to update
            form: Form containing updated company data
            db_session: SQLAlchemy session

        Returns:
            Updated company object
        """
        company.name = form.name.data
        company.legal_name = form.legal_name.data
        company.tax_id = form.tax_id.data
        company.address = form.address.data
        company.phone = form.phone.data
        company.email = form.email.data
        company.website = form.website.data

        db_session.commit()
        log_action(ActionType.UPDATE, f"Updated company {company.name}", db_session)

        return company

    @staticmethod
    def get_company_metrics(company, db_session):
        """
        Get metrics for a company

        Args:
            company: Company object
            db_session: SQLAlchemy session

        Returns:
            Dictionary with company metrics
        """
        # Get company-related statistics
        manager_count = db_session.query(Manager).filter_by(company_id=company.id).count()
        operator_count = db_session.query(Operator).filter_by(company_id=company.id).count()
        driver_count = db_session.query(Driver).filter_by(company_id=company.id).count()

        # Get task statistics
        task_ids = db_session.query(Task.id) \
            .join(User, Task.creator_id == User.id) \
            .join(Manager, User.id == Manager.id) \
            .filter(Manager.company_id == company.id).all()
        task_ids = [t[0] for t in task_ids]

        task_count = len(task_ids)
        completed_tasks = db_session.query(Task) \
            .filter(Task.id.in_(task_ids), Task.status == TaskStatus.COMPLETED).count()
        in_progress_tasks = db_session.query(Task) \
            .filter(Task.id.in_(task_ids), Task.status == TaskStatus.IN_PROGRESS).count()

        return {
            'managers': manager_count,
            'operators': operator_count,
            'drivers': driver_count,
            'tasks': task_count,
            'completed_tasks': completed_tasks,
            'in_progress_tasks': in_progress_tasks,
            'completion_rate': (completed_tasks / task_count * 100) if task_count > 0 else 0
        }


class AuthService:
    @staticmethod
    def login_user(user, db_session):
        """
        Log user login

        Args:
            user: User object
            db_session: SQLAlchemy session
        """
        user.last_login = datetime.utcnow()
        db_session.commit()
        log_action(ActionType.LOGIN, f"User {user.username} logged in", db_session)

    @staticmethod
    def logout_user(user, db_session):
        """
        Log user logout

        Args:
            user: User object
            db_session: SQLAlchemy session
        """
        log_action(ActionType.LOGOUT, f"User {user.username} logged out", db_session)


class LogService:
    @staticmethod
    def get_recent_logs(limit=100, db_session=None):
        """
        Get recent log entries

        Args:
            limit: Maximum number of logs to return
            db_session: SQLAlchemy session

        Returns:
            List of Log objects
        """
        return Log.query.order_by(Log.timestamp.desc()).limit(limit).all()

    @staticmethod
    def get_user_logs(user_id, limit=100, db_session=None):
        """
        Get recent log entries for a specific user

        Args:
            user_id: User ID
            limit: Maximum number of logs to return
            db_session: SQLAlchemy session

        Returns:
            List of Log objects
        """
        return Log.query.filter_by(user_id=user_id).order_by(Log.timestamp.desc()).limit(limit).all()