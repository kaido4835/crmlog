import os
from dotenv import load_dotenv
from app import create_app, db
from models import User, UserRole, Admin, CompanyOwner, Manager, Operator, Driver
from models import Company, Task, TaskStatus, Route, RouteStatus, Document, Log, ActionType, Statistics
from flask import send_from_directory

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
            print(f'Error: {"Username" if existing_user.username == username else "Email"} already exists.')
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
        print(f'Admin user {username} created successfully!')
    except Exception as e:
        db.session.rollback()
        print(f'Error creating admin: {str(e)}')


@app.cli.command('init-db')
def init_db():
    """Initialize database tables"""
    try:
        db.create_all()
        print('Database tables created.')
    except Exception as e:
        print(f'Error initializing database: {str(e)}')


@app.cli.command('create-test-data')
def create_test_data():
    """Create test data for development (use only after init-db)"""
    # Import create_test_data function from init_db.py
    from init_db import create_test_data
    create_test_data()


@app.route('/favicon.ico')
def favicon():
    return '', 204


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)