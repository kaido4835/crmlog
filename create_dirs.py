import os


# Create directories for templates
def create_directories():
    # List of directories to create
    directories = [
        'templates',
        'templates/errors',
        'templates/admin',
        'templates/auth',
        'templates/documents',
        'templates/driver',
        'templates/manager',
        'templates/messages',
        'templates/operator',
        'templates/owner',
        'templates/routes',
        'templates/statistics',
        'templates/tasks',
        'static',
        'static/css',
        'static/js',
        'static/uploads',
        'static/uploads/profile_images',
        'static/uploads/documents',
        'logs'
    ]

    # Create each directory if it doesn't exist
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")
        else:
            print(f"Directory already exists: {directory}")


if __name__ == "__main__":
    create_directories()
    print("Directory structure created successfully!")