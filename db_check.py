#!/usr/bin/env python
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import scoped_session, sessionmaker
import sys

# Get current directory to add to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import models if possible
try:
    from models import User, UserRole, Admin, Company, Task, TaskStatus, Route, RouteStatus, Document, Log, ActionType

    models_imported = True
except ImportError:
    models_imported = False
    print("Warning: Could not import models, using raw SQL queries instead.")

# Database connection parameters
DB_USER = "postgres"
DB_PASSWORD = "mirka2003"
DB_NAME = "crm"
DB_HOST = "localhost"
DB_PORT = "5432"

# Connection string
CONNECTION_STRING = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def test_connection():
    """Test database connection and display PostgreSQL version"""
    try:
        # Create engine
        engine = create_engine(CONNECTION_STRING)

        # Try to connect
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ Successfully connected to PostgreSQL database!")
            print(f"PostgreSQL version: {version}")
            return engine
    except SQLAlchemyError as e:
        print(f"❌ Database connection error: {str(e)}")
        return None


def check_tables(engine):
    """Check if required tables exist in the database"""
    if not engine:
        return

    try:
        with engine.connect() as connection:
            # Check if tables exist
            result = connection.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public';"
            ))
            tables = [row[0] for row in result]

            # Expected tables from models
            expected_tables = [
                'users', 'admins', 'company_owners', 'managers', 'operators', 'drivers',
                'companies', 'tasks', 'routes', 'documents', 'messages', 'logs', 'statistics'
            ]

            print("\n--- Checking tables ---")

            for table in expected_tables:
                if table in tables:
                    print(f"✅ Table '{table}' exists")
                else:
                    print(f"❌ Table '{table}' missing")

            # Check for additional tables
            other_tables = [t for t in tables if t not in expected_tables]
            if other_tables:
                print("\nAdditional tables found:")
                for table in other_tables:
                    print(f"  - {table}")

    except SQLAlchemyError as e:
        print(f"❌ Error checking tables: {str(e)}")


def count_records(engine):
    """Count records in main tables"""
    if not engine:
        return

    try:
        with engine.connect() as connection:
            tables_to_check = [
                'users', 'admins', 'companies', 'tasks', 'routes', 'documents', 'logs'
            ]

            print("\n--- Record counts ---")

            for table in tables_to_check:
                try:
                    result = connection.execute(text(f"SELECT COUNT(*) FROM {table};"))
                    count = result.scalar()
                    print(f"Table '{table}': {count} records")
                except SQLAlchemyError as e:
                    print(f"Error counting records in '{table}': {str(e)}")

    except SQLAlchemyError as e:
        print(f"❌ Error counting records: {str(e)}")


def list_users(engine):
    """List all users in the database"""
    if not engine:
        return

    try:
        with engine.connect() as connection:
            result = connection.execute(text(
                "SELECT id, username, email, role, is_active FROM users ORDER BY id;"
            ))

            users = result.fetchall()

            print("\n--- User list ---")
            if not users:
                print("No users found in the database.")
            else:
                print(f"Found {len(users)} users:")
                print(f"{'ID':4} | {'Username':15} | {'Email':25} | {'Role':15} | {'Active'}")
                print("-" * 70)
                for user in users:
                    print(f"{user[0]:<4} | {user[1]:15} | {user[2]:25} | {user[3]:15} | {user[4]}")

    except SQLAlchemyError as e:
        print(f"❌ Error listing users: {str(e)}")


def list_admins(engine):
    """List all admin users"""
    if not engine:
        return

    try:
        with engine.connect() as connection:
            result = connection.execute(text(
                "SELECT u.id, u.username, u.email, a.admin_level "
                "FROM users u "
                "JOIN admins a ON u.id = a.id "
                "ORDER BY u.id;"
            ))

            admins = result.fetchall()

            print("\n--- Admin users ---")
            if not admins:
                print("No admin users found in the database.")
            else:
                print(f"Found {len(admins)} admin users:")
                print(f"{'ID':4} | {'Username':15} | {'Email':25} | {'Admin Level'}")
                print("-" * 65)
                for admin in admins:
                    print(f"{admin[0]:<4} | {admin[1]:15} | {admin[2]:25} | {admin[3]}")

    except SQLAlchemyError as e:
        print(f"❌ Error listing admins: {str(e)}")


def check_permission_issues(engine):
    """Check for common permission issues"""
    if not engine:
        return

    try:
        with engine.connect() as connection:
            # Check if postgres user has appropriate permissions
            result = connection.execute(text(
                "SELECT has_table_privilege(current_user, 'users', 'SELECT') as can_select, "
                "has_table_privilege(current_user, 'users', 'INSERT') as can_insert, "
                "has_table_privilege(current_user, 'users', 'UPDATE') as can_update, "
                "has_table_privilege(current_user, 'users', 'DELETE') as can_delete;"
            ))

            row = result.fetchone()
            if row:
                print("\n--- Permissions check ---")
                print(f"SELECT permission: {'✅' if row[0] else '❌'}")
                print(f"INSERT permission: {'✅' if row[1] else '❌'}")
                print(f"UPDATE permission: {'✅' if row[2] else '❌'}")
                print(f"DELETE permission: {'✅' if row[3] else '❌'}")

    except SQLAlchemyError as e:
        print(f"❌ Error checking permissions: {str(e)}")


def check_config_file():
    """Check if config.py has the correct database settings"""
    try:
        from config import Config

        print("\n--- Database config check ---")

        # Extract database settings from URI
        db_uri = Config.SQLALCHEMY_DATABASE_URI
        print(f"Database URI in config.py: {db_uri}")

        # Check if URI matches our connection parameters
        expected_uri = CONNECTION_STRING
        if db_uri == expected_uri:
            print("✅ Database URI in config.py matches the expected connection string")
        else:
            print("❌ Database URI in config.py does not match the expected connection string")
            print(f"Expected: {expected_uri}")

    except (ImportError, AttributeError) as e:
        print(f"❌ Error checking config.py: {str(e)}")


def main():
    """Main function to run all diagnostics"""
    print("=== Database Connection Diagnostic Tool ===\n")

    # Test connection
    engine = test_connection()

    if engine:
        # Check config file
        check_config_file()

        # Check tables
        check_tables(engine)

        # Count records
        count_records(engine)

        # List users
        list_users(engine)

        # List admins
        list_admins(engine)

        # Check permission issues
        check_permission_issues(engine)

        print("\n=== Diagnostics completed ===")
    else:
        print("\n❌ Cannot continue diagnostics due to connection error.")
        print("Please check database connection parameters and try again.")


if __name__ == "__main__":
    main()