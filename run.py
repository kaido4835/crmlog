import os
from dotenv import load_dotenv
from app import create_app, db
from models import User, UserRole, Admin, CompanyOwner, Manager, Operator, Driver
from models import Company, Task, TaskStatus, Route, RouteStatus, Document, Log, ActionType, Statistics
import datetime

# Load environment variables from .env file if it exists
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# Create app instance
app = create_app(os.getenv('FLASK_CONFIG') or 'default')


@app.shell_context_processor
def make_shell_context():
    """
    Make important objects available in the interactive shell
    """
    return {
        'db': db,
        'User': User,
        'UserRole': UserRole,
        'Admin': Admin,
        'CompanyOwner': CompanyOwner,
        'Manager': Manager,
        'Operator': Operator,
        'Driver': Driver,
        'Company': Company,
        'Task': Task,
        'TaskStatus': TaskStatus,
        'Route': Route,
        'RouteStatus': RouteStatus,
        'Document': Document,
        'Log': Log,
        'ActionType': ActionType,
        'Statistics': Statistics
    }


@app.cli.command('create-admin')
def create_admin():
    """Create admin user for initial setup"""
    app.logger.info("Starting create-admin command")
    username = input('Admin username: ')
    email = input('Admin email: ')
    password = input('Admin password: ')
    first_name = input('First name: ')
    last_name = input('Last name: ')

    try:
        # Check if admin already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            error_msg = f'Error: {"Username" if existing_user.username == username else "Email"} already exists.'
            app.logger.error(error_msg)
            print(error_msg)
            return

        # Create user
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=UserRole.ADMIN,
            is_active=True
        )
        user.set_password(password)

        db.session.add(user)
        db.session.flush()  # Get user ID

        # Create admin
        admin = Admin(id=user.id, admin_level=2)  # Highest admin level
        db.session.add(admin)

        db.session.commit()
        success_msg = f'Admin user {username} created successfully!'
        app.logger.info(success_msg)
        print(success_msg)
    except Exception as e:
        db.session.rollback()
        error_msg = f'Error creating admin: {str(e)}'
        app.logger.error(error_msg)
        print(error_msg)


@app.cli.command('init-db')
def init_db():
    """Initialize database tables"""
    app.logger.info("Starting init-db command")
    try:
        db.create_all()
        success_msg = 'Database tables created.'
        app.logger.info(success_msg)
        print(success_msg)
    except Exception as e:
        error_msg = f'Error initializing database: {str(e)}'
        app.logger.error(error_msg)
        print(error_msg)


@app.cli.command('create-test-data')
def create_test_data():
    """Create test data for development (use only after init-db)"""
    app.logger.info("Starting create-test-data command")
    # Import create_test_data function from init_db.py
    try:
        from init_db import create_test_data
        create_test_data()
        app.logger.info("Test data creation completed")
    except Exception as e:
        error_msg = f'Error creating test data: {str(e)}'
        app.logger.error(error_msg)
        print(error_msg)


if __name__ == '__main__':
    # Log startup information
    now = datetime.datetime.now()
    startup_message = f"============ CRM APPLICATION STARTED AT {now.strftime('%Y-%m-%d %H:%M:%S')} ============"
    app.logger.info(startup_message)
    app.logger.info(f"Running with configuration: {os.getenv('FLASK_CONFIG') or 'default'}")
    app.logger.info(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

    app.run(host='0.0.0.0', debug=True)