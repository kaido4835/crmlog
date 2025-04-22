#!/usr/bin/env python
"""
Test data generator for CRM system
This script creates a minimal set of test data for the CRM application
"""
import os
import sys
import random
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import necessary components from the application
try:
    from app import db, create_app
    from models import (
        User, UserRole, Admin, CompanyOwner, Manager, Operator, Driver,
        Company, Task, TaskStatus, Route, RouteStatus, Document, Message, Log, ActionType
    )
except ImportError as e:
    print(f"Error importing application modules: {e}")
    print("Make sure you're running this script from the project root directory")
    sys.exit(1)

# Create Flask app context
app = create_app('development')

# Sample data for generation
COMPANY_NAMES = [
    "FastTrack Logistics", "Urban Delivery Co.", "Express Cargo Systems",
    "Metropolitan Transport", "City Courier Services"
]

FIRST_NAMES = [
    "John", "Jane", "Michael", "Sarah", "Robert", "Emily", "David", "Lisa",
    "Mark", "Anna", "Thomas", "Laura", "James", "Maria", "Alexander", "Olivia"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Garcia",
    "Rodriguez", "Wilson", "Martinez", "Anderson", "Taylor", "Thomas", "Moore", "Jackson"
]

ADDRESSES = [
    "123 Main St, Cityville", "456 Oak Ave, Townsburg", "789 Pine Rd, Villageton",
    "321 Maple Dr, Hamletville", "654 Cedar Ln, Boroughtown", "987 Birch Blvd, Districtville"
]

TASK_TITLES = [
    "Delivery to downtown office", "Package pickup from warehouse", "Express delivery to airport",
    "Document transport to headquarters", "Equipment delivery to construction site",
    "Catering delivery to event venue", "Medical supplies transport", "Retail stock delivery"
]

ROUTE_LOCATIONS = [
    "Central Station", "North Industrial Park", "West Side Mall", "East End Hospital",
    "South Business District", "Airport Terminal", "University Campus", "Downtown Plaza",
    "Riverside Warehouse", "Hillside Residential Area", "Tech Park", "Harbor Terminal"
]

VEHICLE_TYPES = [
    "Ford Transit Van", "Mercedes Sprinter", "Toyota HiAce", "Volkswagen Crafter",
    "Renault Master", "Nissan NV200", "Fiat Ducato", "Peugeot Boxer"
]


def clean_database():
    """Remove all existing data from the database (except admin users)"""
    print("Cleaning database...")
    try:
        # Preserve existing admin users
        admin_ids = [admin.id for admin in Admin.query.all()]

        # Delete all data from tables in correct order to avoid foreign key constraints
        Message.query.delete()
        Document.query.delete()
        Route.query.delete()
        Task.query.delete()
        Log.query.delete()

        # Delete user role-specific data, except for admins
        Driver.query.filter(Driver.id.notin_(admin_ids)).delete(synchronize_session=False)
        Operator.query.filter(Operator.id.notin_(admin_ids)).delete(synchronize_session=False)
        Manager.query.filter(Manager.id.notin_(admin_ids)).delete(synchronize_session=False)
        CompanyOwner.query.filter(CompanyOwner.id.notin_(admin_ids)).delete(synchronize_session=False)

        # Delete regular users, except for admins
        User.query.filter(User.id.notin_(admin_ids)).delete(synchronize_session=False)

        # Delete all companies
        Company.query.delete()

        db.session.commit()
        print("Database cleaned successfully.")
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error cleaning database: {e}")
        return False
    return True


def create_companies(count=3):
    """Create test companies"""
    print(f"Creating {count} companies...")
    companies = []

    for i in range(count):
        company_name = COMPANY_NAMES[i % len(COMPANY_NAMES)]
        legal_name = f"{company_name}, LLC" if i % 2 == 0 else f"{company_name}, Inc."

        company = Company(
            name=f"{company_name} {i + 1}",
            legal_name=legal_name,
            tax_id=f"TAX-{100000 + i * 1111}",
            address=random.choice(ADDRESSES),
            phone=f"+1 555-{1000 + i * 100:04d}",
            email=f"info@{company_name.lower().replace(' ', '')}{i + 1}.com",
            website=f"www.{company_name.lower().replace(' ', '')}{i + 1}.com",
            created_at=datetime.utcnow()
        )

        db.session.add(company)
        companies.append(company)

    try:
        db.session.commit()
        print(f"Created {len(companies)} companies.")
        return companies
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error creating companies: {e}")
        return []


def create_company_owners(companies):
    """Create company owners for each company"""
    print("Creating company owners...")
    company_owners = []

    for i, company in enumerate(companies):
        # Create user
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        username = f"owner{i + 1}"

        user = User(
            username=username,
            email=f"{username}@{company.name.lower().replace(' ', '')}.com",
            password_hash=generate_password_hash("password123"),
            first_name=first_name,
            last_name=last_name,
            phone=f"+1 555-{2000 + i * 100:04d}",
            role=UserRole.COMPANY_OWNER,
            is_active=True,
            created_at=datetime.utcnow()
        )

        db.session.add(user)
        db.session.flush()  # Get user ID

        # Create company owner
        company_owner = CompanyOwner(
            id=user.id,
            company_id=company.id
        )

        db.session.add(company_owner)
        company_owners.append((user, company_owner))

        print(f"Created company owner: {username} for {company.name}")

    try:
        db.session.commit()
        print(f"Created {len(company_owners)} company owners.")
        return company_owners
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error creating company owners: {e}")
        return []


def create_managers(companies, count_per_company=2):
    """Create managers for each company"""
    print(f"Creating {count_per_company} managers per company...")
    managers = []

    for company in companies:
        for i in range(count_per_company):
            # Create user
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            username = f"manager{company.id}_{i + 1}"

            user = User(
                username=username,
                email=f"{username}@{company.name.lower().replace(' ', '')}.com",
                password_hash=generate_password_hash("password123"),
                first_name=first_name,
                last_name=last_name,
                phone=f"+1 555-{3000 + len(managers) * 100:04d}",
                role=UserRole.MANAGER,
                is_active=True,
                created_at=datetime.utcnow()
            )

            db.session.add(user)
            db.session.flush()  # Get user ID

            # Create manager
            manager = Manager(
                id=user.id,
                company_id=company.id
            )

            db.session.add(manager)
            managers.append((user, manager))

    try:
        db.session.commit()
        print(f"Created {len(managers)} managers.")
        return managers
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error creating managers: {e}")
        return []


def create_operators(managers, count_per_manager=2):
    """Create operators for each manager"""
    print(f"Creating {count_per_manager} operators per manager...")
    operators = []

    for user, manager in managers:
        company_id = manager.company_id
        company = Company.query.get(company_id)

        for i in range(count_per_manager):
            # Create user
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            username = f"operator{manager.id}_{i + 1}"

            user = User(
                username=username,
                email=f"{username}@{company.name.lower().replace(' ', '')}.com",
                password_hash=generate_password_hash("password123"),
                first_name=first_name,
                last_name=last_name,
                phone=f"+1 555-{4000 + len(operators) * 100:04d}",
                role=UserRole.OPERATOR,
                is_active=True,
                created_at=datetime.utcnow()
            )

            db.session.add(user)
            db.session.flush()  # Get user ID

            # Create operator
            operator = Operator(
                id=user.id,
                company_id=company_id,
                manager_id=manager.id
            )

            db.session.add(operator)
            operators.append((user, operator))

    try:
        db.session.commit()
        print(f"Created {len(operators)} operators.")
        return operators
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error creating operators: {e}")
        return []


def create_drivers(operators, count_per_operator=3):
    """Create drivers for each operator"""
    print(f"Creating {count_per_operator} drivers per operator...")
    drivers = []

    for user, operator in operators:
        company_id = operator.company_id
        company = Company.query.get(company_id)

        for i in range(count_per_operator):
            # Create user
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            username = f"driver{operator.id}_{i + 1}"

            user = User(
                username=username,
                email=f"{username}@{company.name.lower().replace(' ', '')}.com",
                password_hash=generate_password_hash("password123"),
                first_name=first_name,
                last_name=last_name,
                phone=f"+1 555-{5000 + len(drivers) * 100:04d}",
                role=UserRole.DRIVER,
                is_active=True,
                created_at=datetime.utcnow()
            )

            db.session.add(user)
            db.session.flush()  # Get user ID

            # Create driver
            license_number = f"DL-{100000 + len(drivers) * 111}"
            vehicle = random.choice(VEHICLE_TYPES)

            driver = Driver(
                id=user.id,
                company_id=company_id,
                operator_id=operator.id,
                license_number=license_number,
                vehicle_info=vehicle
            )

            db.session.add(driver)
            drivers.append((user, driver))

    try:
        db.session.commit()
        print(f"Created {len(drivers)} drivers.")
        return drivers
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error creating drivers: {e}")
        return []


def create_tasks(companies, operators, drivers, count_per_company=5):
    """Create tasks for each company"""
    print(f"Creating {count_per_company} tasks per company...")
    tasks = []

    for company in companies:
        # Get operators and drivers for this company
        company_operators = [(u, o) for u, o in operators if o.company_id == company.id]
        company_drivers = [(u, d) for u, d in drivers if d.company_id == company.id]

        if not company_operators or not company_drivers:
            print(f"Skipping tasks for company {company.name} due to missing operators or drivers")
            continue

        for i in range(count_per_company):
            # Select random operator as creator
            operator_user, operator = random.choice(company_operators)

            # Select random driver as assignee
            driver_user, driver = random.choice(company_drivers)

            # Create task
            title = random.choice(TASK_TITLES)
            status = random.choice(list(TaskStatus))

            # Set deadline between now and 10 days from now
            days_ahead = random.randint(1, 10)
            deadline = datetime.utcnow() + timedelta(days=days_ahead)

            task = Task(
                title=f"{title} #{i + 1}",
                description=f"Task description for {title} #{i + 1}. Created for testing purposes.",
                status=status,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                deadline=deadline,
                company_id=company.id,
                creator_id=operator_user.id,
                assignee_id=driver_user.id
            )

            db.session.add(task)
            tasks.append(task)

    try:
        db.session.commit()
        print(f"Created {len(tasks)} tasks.")
        return tasks
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error creating tasks: {e}")
        return []


def create_routes(tasks, drivers):
    """Create routes for tasks"""
    print("Creating routes for tasks...")
    routes = []

    # Dict to look up driver by user_id
    driver_by_user_id = {user.id: driver for user, driver in drivers}

    for task in tasks:
        # Only create routes for tasks with assignees
        if not task.assignee_id or task.assignee_id not in driver_by_user_id:
            continue

        driver = driver_by_user_id[task.assignee_id]

        # Set route status based on task status
        if task.status == TaskStatus.COMPLETED:
            route_status = RouteStatus.COMPLETED
        elif task.status == TaskStatus.IN_PROGRESS:
            route_status = RouteStatus.IN_PROGRESS
        else:
            route_status = RouteStatus.PLANNED

        # Set start and end locations
        start_location = random.choice(ROUTE_LOCATIONS)
        end_location = random.choice([loc for loc in ROUTE_LOCATIONS if loc != start_location])

        # Generate some waypoints (2-4)
        waypoint_count = random.randint(2, 4)
        waypoints = []

        for i in range(waypoint_count):
            waypoint = {
                "location": random.choice(ROUTE_LOCATIONS),
                "order": i + 1,
                "completed": route_status == RouteStatus.COMPLETED or (
                        route_status == RouteStatus.IN_PROGRESS and random.random() > 0.5
                )
            }
            waypoints.append(waypoint)

        # Calculate distance (10-100 km)
        distance = round(random.uniform(10, 100), 1)

        # Calculate estimated time (in minutes, based on distance)
        estimated_time = int(distance * 2)  # 2 minutes per km

        # Set start time in the future for planned routes
        # or in the past for in-progress or completed routes
        if route_status == RouteStatus.PLANNED:
            start_time = datetime.utcnow() + timedelta(days=random.randint(1, 5))
        else:
            start_time = datetime.utcnow() - timedelta(days=random.randint(1, 5))

        # Set end time for completed routes
        end_time = None
        if route_status == RouteStatus.COMPLETED:
            end_time = start_time + timedelta(minutes=estimated_time)

        route = Route(
            start_point=start_location,
            end_point=end_location,
            waypoints=waypoints,
            distance=distance,
            estimated_time=estimated_time,
            status=route_status,
            start_time=start_time,
            end_time=end_time,
            driver_id=driver.id,
            task_id=task.id,
            company_id=task.company_id,
            created_at=datetime.utcnow()
        )

        db.session.add(route)
        routes.append(route)

    try:
        db.session.commit()
        print(f"Created {len(routes)} routes.")
        return routes
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error creating routes: {e}")
        return []


def create_logs(users, count=50):
    """Create some system logs"""
    print(f"Creating {count} log entries...")
    logs = []

    for i in range(count):
        # Choose random user
        user = random.choice([u for u, _ in users])

        # Determine company_id based on user role
        company_id = None
        if user.role == UserRole.COMPANY_OWNER:
            company_id = user.company_owner.company_id
        elif user.role == UserRole.MANAGER:
            company_id = user.manager.company_id
        elif user.role == UserRole.OPERATOR:
            company_id = user.operator.company_id
        elif user.role == UserRole.DRIVER:
            company_id = user.driver.company_id

        # Choose random action type
        action_type = random.choice(list(ActionType))

        # Create description based on action type
        if action_type == ActionType.LOGIN:
            description = f"User {user.username} logged in"
        elif action_type == ActionType.LOGOUT:
            description = f"User {user.username} logged out"
        elif action_type == ActionType.CREATE:
            description = f"User {user.username} created a new task"
        elif action_type == ActionType.UPDATE:
            description = f"User {user.username} updated a task"
        elif action_type == ActionType.DELETE:
            description = f"User {user.username} deleted a task"
        elif action_type == ActionType.VIEW:
            description = f"User {user.username} viewed a task"
        else:
            description = f"User {user.username} performed action {action_type.value}"

        # Set timestamp within the last week
        timestamp = datetime.utcnow() - timedelta(
            days=random.randint(0, 7),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )

        log = Log(
            action_type=action_type,
            description=description,
            timestamp=timestamp,
            ip_address=f"192.168.1.{random.randint(1, 255)}",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            user_id=user.id,
            company_id=company_id
        )

        db.session.add(log)
        logs.append(log)

    try:
        db.session.commit()
        print(f"Created {len(logs)} log entries.")
        return logs
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error creating logs: {e}")
        return []


def create_messages(users, tasks, count=30):
    """Create messages between users"""
    print(f"Creating {count} messages...")
    messages = []

    for i in range(count):
        # Choose random sender and recipient (different users)
        sender_user, _ = random.choice(users)
        recipient_user, _ = random.choice([u for u in users if u[0].id != sender_user.id])

        # Determine company_id based on sender role
        company_id = None
        if sender_user.role == UserRole.COMPANY_OWNER and hasattr(sender_user, 'company_owner'):
            company_id = sender_user.company_owner.company_id
        elif sender_user.role == UserRole.MANAGER and hasattr(sender_user, 'manager'):
            company_id = sender_user.manager.company_id
        elif sender_user.role == UserRole.OPERATOR and hasattr(sender_user, 'operator'):
            company_id = sender_user.operator.company_id
        elif sender_user.role == UserRole.DRIVER and hasattr(sender_user, 'driver'):
            company_id = sender_user.driver.company_id

        # Choose random task sometimes (30% of the time)
        task_id = random.choice(tasks).id if tasks and random.random() < 0.3 else None

        # Set sent time within the last week
        sent_at = datetime.utcnow() - timedelta(
            days=random.randint(0, 7),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )

        # Determine if message is read (older messages are more likely to be read)
        days_old = (datetime.utcnow() - sent_at).days
        is_read = random.random() < (days_old / 7)  # Probability increases with age

        message = Message(
            content=f"This is test message #{i + 1} from {sender_user.username} to {recipient_user.username}.",
            sent_at=sent_at,
            is_read=is_read,
            sender_id=sender_user.id,
            recipient_id=recipient_user.id,
            task_id=task_id,
            company_id=company_id
        )

        db.session.add(message)
        messages.append(message)

    try:
        db.session.commit()
        print(f"Created {len(messages)} messages.")
        return messages
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error creating messages: {e}")
        return []


def main():
    print("=== CRM Test Data Generator ===")

    with app.app_context():
        # Clean database, but preserve admin users
        if not clean_database():
            return

        # Create companies
        companies = create_companies(count=3)
        if not companies:
            return

        # Create users of different roles
        company_owners = create_company_owners(companies)
        if not company_owners:
            return

        managers = create_managers(companies, count_per_company=2)
        if not managers:
            return

        operators = create_operators(managers, count_per_manager=2)
        if not operators:
            return

        drivers = create_drivers(operators, count_per_operator=2)
        if not drivers:
            return

        # Combine all users for later use
        all_users = company_owners + managers + operators + drivers

        # Create tasks
        tasks = create_tasks(companies, operators, drivers, count_per_company=5)
        if not tasks:
            return

        # Create routes
        routes = create_routes(tasks, drivers)

        # Create logs
        logs = create_logs(all_users, count=50)

        # Create messages
        messages = create_messages(all_users, tasks, count=30)

        print("\n=== Test data generation completed successfully ===")
        print(f"Created: {len(companies)} companies, {len(all_users)} users, {len(tasks)} tasks, {len(routes)} routes")
        print(f"Login with any user using password: password123")


if __name__ == "__main__":
    main()