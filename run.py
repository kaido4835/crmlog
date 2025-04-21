import os
from dotenv import load_dotenv
from app import create_app, db
from models import User, UserRole, Admin, CompanyOwner, Manager, Operator, Driver
from models import Company, Task, TaskStatus, Route, RouteStatus
from datetime import datetime
from werkzeug.security import generate_password_hash

# Load environment variables from .env file if it exists
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# Create app instance
app = create_app(os.getenv('FLASK_CONFIG') or 'default')


@app.before_first_request
def before_first_request():
    """
    Initialize database before the first request if tables don't exist
    """
    with app.app_context():
        # Check if tables need to be created
        if not db.engine.dialect.has_table(db.engine, 'users'):
            app.logger.info("Creating database tables...")
            db.create_all()
            app.logger.info("Database tables created successfully.")

            # Create admin user if no users exist
            if User.query.count() == 0:
                app.logger.info("Creating initial admin user...")

                # Create user with admin role
                admin_user = User(
                    username="admin",
                    email="admin@example.com",
                    first_name="Admin",
                    last_name="User",
                    password_hash=generate_password_hash("admin123"),  # Default password
                    role=UserRole.ADMIN,
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )

                db.session.add(admin_user)
                db.session.flush()  # Get user ID

                # Create admin record
                admin = Admin(
                    id=admin_user.id,
                    admin_level=2  # Highest admin level
                )

                db.session.add(admin)
                db.session.commit()
                app.logger.info("Initial admin user created successfully.")

            # Create test data in development mode
            if app.config.get('DEBUG', False) and Company.query.filter_by(name="Test Company").first() is None:
                app.logger.info("Creating test data...")

                # Create test company
                company = Company(
                    name="Test Company",
                    legal_name="Test Company LLC",
                    tax_id="123456789",
                    address="123 Test Street",
                    phone="555-123-4567",
                    email="info@testcompany.com",
                    website="www.testcompany.com",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.session.add(company)
                db.session.flush()

                # Create company owner
                owner_user = User(
                    username="owner",
                    email="owner@testcompany.com",
                    first_name="Company",
                    last_name="Owner",
                    password_hash=generate_password_hash("password"),
                    role=UserRole.COMPANY_OWNER,
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.session.add(owner_user)
                db.session.flush()

                owner = CompanyOwner(
                    id=owner_user.id,
                    company_id=company.id
                )
                db.session.add(owner)

                # Create manager
                manager_user = User(
                    username="manager",
                    email="manager@testcompany.com",
                    first_name="Test",
                    last_name="Manager",
                    password_hash=generate_password_hash("password"),
                    role=UserRole.MANAGER,
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.session.add(manager_user)
                db.session.flush()

                manager = Manager(
                    id=manager_user.id,
                    company_id=company.id
                )
                db.session.add(manager)

                # Create operator
                operator_user = User(
                    username="operator",
                    email="operator@testcompany.com",
                    first_name="Test",
                    last_name="Operator",
                    password_hash=generate_password_hash("password"),
                    role=UserRole.OPERATOR,
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.session.add(operator_user)
                db.session.flush()

                operator = Operator(
                    id=operator_user.id,
                    company_id=company.id,
                    manager_id=manager.id
                )
                db.session.add(operator)

                # Create driver
                driver_user = User(
                    username="driver",
                    email="driver@testcompany.com",
                    first_name="Test",
                    last_name="Driver",
                    password_hash=generate_password_hash("password"),
                    role=UserRole.DRIVER,
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.session.add(driver_user)
                db.session.flush()

                driver = Driver(
                    id=driver_user.id,
                    company_id=company.id,
                    operator_id=operator.id,
                    license_number="DL123456",
                    vehicle_info="Truck #1"
                )
                db.session.add(driver)

                # Create task
                task = Task(
                    title="Test Delivery",
                    description="Deliver test package to client",
                    status=TaskStatus.NEW,
                    creator_id=operator_user.id,
                    assignee_id=driver_user.id,
                    company_id=company.id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.session.add(task)
                db.session.flush()

                # Create route
                route = Route(
                    start_point="Warehouse A",
                    end_point="Client Office",
                    distance=25.5,
                    estimated_time=60,  # 60 minutes
                    status=RouteStatus.PLANNED,
                    driver_id=driver.id,
                    task_id=task.id,
                    company_id=company.id,
                    created_at=datetime.utcnow()
                )
                db.session.add(route)

                db.session.commit()
                app.logger.info("Test data created successfully.")
        else:
            app.logger.info("Database tables already exist.")


@app.shell_context_processor
def make_shell_context():
    """
    Make important objects available in the interactive shell
    """
    from models import (
        User, UserRole, Admin, CompanyOwner, Manager, Operator, Driver,
        Company, Task, TaskStatus, Route, RouteStatus, Document, Log, ActionType, Statistics
    )
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
    """Create test data for development"""
    try:
        # Check if we already have test data
        if Company.query.filter_by(name="Test Company").first():
            print("Test data already exists.")
            return

        print("Creating test data...")

        # Create test company
        company = Company(
            name="Test Company",
            legal_name="Test Company LLC",
            tax_id="123456789",
            address="123 Test Street",
            phone="555-123-4567",
            email="info@testcompany.com",
            website="www.testcompany.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(company)
        db.session.flush()

        # Create company owner
        owner_user = User(
            username="owner",
            email="owner@testcompany.com",
            first_name="Company",
            last_name="Owner",
            password_hash=generate_password_hash("password"),
            role=UserRole.COMPANY_OWNER,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(owner_user)
        db.session.flush()

        owner = CompanyOwner(
            id=owner_user.id,
            company_id=company.id
        )
        db.session.add(owner)

        print('Company owner created.')

        # Create manager
        manager_user = User(
            username="manager",
            email="manager@testcompany.com",
            first_name="Test",
            last_name="Manager",
            password_hash=generate_password_hash("password"),
            role=UserRole.MANAGER,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(manager_user)
        db.session.flush()

        manager = Manager(
            id=manager_user.id,
            company_id=company.id
        )
        db.session.add(manager)

        print('Manager created.')

        # Create operator
        operator_user = User(
            username="operator",
            email="operator@testcompany.com",
            first_name="Test",
            last_name="Operator",
            password_hash=generate_password_hash("password"),
            role=UserRole.OPERATOR,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(operator_user)
        db.session.flush()

        operator = Operator(
            id=operator_user.id,
            company_id=company.id,
            manager_id=manager.id
        )
        db.session.add(operator)

        print('Operator created.')

        # Create driver
        driver_user = User(
            username="driver",
            email="driver@testcompany.com",
            first_name="Test",
            last_name="Driver",
            password_hash=generate_password_hash("password"),
            role=UserRole.DRIVER,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(driver_user)
        db.session.flush()

        driver = Driver(
            id=driver_user.id,
            company_id=company.id,
            operator_id=operator.id,
            license_number="DL123456",
            vehicle_info="Truck #1"
        )
        db.session.add(driver)

        print('Driver created.')

        # Create task
        task = Task(
            title="Test Delivery",
            description="Deliver test package to client",
            status=TaskStatus.NEW,
            creator_id=operator_user.id,
            assignee_id=driver_user.id,
            company_id=company.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(task)
        db.session.flush()

        print('Task created.')

        # Create route
        route = Route(
            start_point="Warehouse A",
            end_point="Client Office",
            distance=25.5,
            estimated_time=60,  # 60 minutes
            status=RouteStatus.PLANNED,
            driver_id=driver.id,
            task_id=task.id,
            company_id=company.id,
            created_at=datetime.utcnow()
        )
        db.session.add(route)

        print('Route created.')

        db.session.commit()
        print('Test data created successfully!')
    except Exception as e:
        db.session.rollback()
        print(f'Error creating test data: {str(e)}')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)