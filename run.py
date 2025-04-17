import os
from dotenv import load_dotenv
from app import create_app, db
from models import User, UserRole, Admin

# Load environment variables from .env file if it exists
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# Create app instance
app = create_app(os.getenv('FLASK_CONFIG') or 'default')


@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'UserRole': UserRole,
        'Admin': Admin
    }


@app.cli.command('create-admin')
def create_admin():
    """Create admin user for initial setup"""
    username = input('Admin username: ')
    email = input('Admin email: ')
    password = input('Admin password: ')
    first_name = input('First name: ')
    last_name = input('Last name: ')

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

    admin = Admin(id=user.id, admin_level=2)  # Highest admin level
    db.session.add(admin)

    db.session.commit()
    print(f'Admin user {username} created successfully!')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)