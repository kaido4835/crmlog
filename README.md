# Logistics CRM System

A comprehensive Customer Relationship Management system designed specifically for logistics and transportation companies. This web-based application streamlines operations, manages teams, tracks tasks, and provides performance analytics for efficient business management.

## 🚀 Features

### Core Functionality
- **User Management** - Role-based permissions system with 5 distinct user roles
- **Task Assignment & Tracking** - Create, assign, and monitor logistics tasks
- **Route Planning** - Optimize delivery routes and track driver progress  
- **Document Management** - Upload and manage shipment documents
- **Real-time Communication** - Chat system between operators and drivers
- **Performance Analytics** - Comprehensive reporting and metrics dashboard

### User Roles & Permissions
- **Admin** - System setup, user management, company registration
- **Company Owner** - Manager oversight, company performance tracking
- **Manager** - Operator team management, task oversight
- **Operator** - Driver coordination, route planning, document handling
- **Driver** - Task execution, route navigation, status updates

## 🛠️ Technology Stack

- **Backend**: Python Flask
- **Database**: PostgreSQL
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Authentication**: Flask-Login
- **Forms**: WTForms
- **File Handling**: Custom document management system
- **Icons**: Font Awesome 6.0

## 📋 Requirements

- Python 3.8+
- PostgreSQL 12+
- pip (Python package manager)

## ⚙️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/kaido4835/logistics-crm.git
   cd logistics-crm
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL database**
   ```sql
   CREATE DATABASE crm;
   CREATE USER your_username WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE crm TO your_username;
   ```

5. **Configure environment variables**
   Create a `.env` file in the root directory:
   ```env
   DATABASE_URL=postgresql://your_username:your_password@localhost/crm
   SECRET_KEY=your-secret-key-here
   FLASK_ENV=development
   ```

6. **Initialize the database**
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

7. **Run the application**
   ```bash
   flask run
   ```

The application will be available at `http://localhost:5000`

## 🗄️ Database Configuration

### Connection Parameters:
- **Username**: your_username
- **Password**: your_password
- **Database**: crm
- **Host**: localhost
- **Port**: 5432

> **Note**: Replace the database credentials with your own PostgreSQL setup.

## 📁 Project Structure

```
logistics-crm/
├── models/               # Database models
│   ├── __init__.py      # Models initialization
│   ├── users.py         # User, role, company models
│   └── operations.py    # Task, route, document models
├── views/               # Route handlers (Blueprints)
│   ├── __init__.py     
│   ├── admin.py         # Admin panel routes
│   ├── auth.py          # Authentication routes
│   ├── documents.py     # Document management routes
│   ├── driver.py        # Driver-specific routes
│   ├── main.py          # Main application routes
│   ├── messages.py      # Messaging system routes
│   ├── operator.py      # Operator-specific routes
│   ├── routes.py        # Route management routes
│   ├── statistics.py    # Analytics and reporting routes
│   └── tasks.py         # Task management routes
├── templates/           # HTML templates
│   ├── base.html        # Base template
│   ├── index.html       # Homepage
│   ├── auth/            # Authentication templates
│   ├── admin/           # Admin panel templates
│   ├── driver/          # Driver dashboard templates
│   ├── operator/        # Operator dashboard templates
│   ├── owner/           # Company owner templates
│   ├── manager/         # Manager dashboard templates
│   ├── tasks/           # Task-related templates
│   ├── documents/       # Document management templates
│   ├── messages/        # Messaging templates
│   └── errors/          # Error page templates
├── static/              # Static files
│   ├── css/            # Stylesheets
│   │   └── style.css   # Custom styles
│   ├── js/             # JavaScript files
│   └── uploads/        # File upload directory
│       └── documents/  # Document storage
├── migrations/          # Database migrations
├── logs/               # Application logs
│   └── crm.log        # Main log file
├── app.py              # Application factory
├── config.py           # Application configuration
├── forms.py            # WTForms form classes
├── services.py         # Business logic services
├── utils.py            # Utility functions
├── jinja2_filters.py   # Custom Jinja2 filters
├── requirements.txt    # Python dependencies
├── run.py             # Application entry point
└── README.md          # This file
```

## 🚦 Getting Started

### First Time Setup

1. **Create Admin User**
   After running the application, register the first user who will automatically become an admin.

2. **Register Companies**
   As an admin, register logistics companies in the system.

3. **Add Company Owners**
   Assign company owners to manage their respective organizations.

4. **Build Teams**
   Company owners can add managers, operators, and drivers to their teams.

5. **Start Operations**
   Operators can now create tasks and assign them to drivers with optimized routes.

### Workflow Example

1. **Operator** creates a delivery task with pickup and destination points
2. **System** suggests optimal route and assigns available driver
3. **Driver** receives task notification and route details
4. **Driver** updates task status throughout delivery process
5. **Operator** monitors progress and handles any issues
6. **Manager** reviews completion metrics and performance data

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://your_username:your_password@localhost/crm` |
| `SECRET_KEY` | Flask secret key for sessions | Required |
| `FLASK_ENV` | Flask environment | `production` |
| `UPLOAD_FOLDER` | Directory for file uploads | `static/uploads` |
| `MAX_CONTENT_LENGTH` | Maximum file upload size | `16MB` |

### Database Schema

The application uses the following main tables:
- `users` - User accounts and authentication
- `companies` - Company information
- `tasks` - Logistics tasks and assignments
- `routes` - Delivery routes and waypoints
- `documents` - File attachments and documentation
- `action_logs` - System activity logging

## 📊 API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `POST /auth/register` - User registration

### Tasks
- `GET /tasks` - List all tasks
- `POST /tasks/create` - Create new task
- `GET /tasks/<id>` - View task details
- `PUT /tasks/<id>` - Update task
- `POST /tasks/<id>/complete` - Mark task as completed

### Users
- `GET /users` - List users (admin only)
- `POST /users/create` - Create new user
- `GET /users/<id>` - View user profile
- `PUT /users/<id>` - Update user

## 🧪 Testing

Run the test suite:
```bash
python -m pytest tests/
```

Run with coverage:
```bash
python -m pytest --cov=app tests/
```

## 🚀 Deployment

### Production Deployment

1. **Set production environment**
   ```bash
   export FLASK_ENV=production
   ```

2. **Configure production database**
   Update `DATABASE_URL` with production PostgreSQL credentials

3. **Set up web server**
   Use Gunicorn with Nginx for production deployment:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 run:app
   ```

4. **Configure Nginx**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Write tests for new features

## 👥 Authors

- **Mironshoh Rahmatullaev** - *Initial work* - [GitHub](https://github.com/kaido4835) | [LinkedIn](https://www.linkedin.com/in/mironshoh-rahmatullaev-531197237/)

## 📚 Academic Project

This project was developed as a diploma thesis for educational purposes, demonstrating the implementation of a comprehensive logistics management system using modern web technologies.

## 🆘 Support

If you encounter any issues or have questions:
Contact me directly:
   - **Telegram**: [@nacht003](https://t.me/nacht003)
   - **LinkedIn**: [Mironshoh Rahmatullaev](https://www.linkedin.com/in/mironshoh-rahmatullaev-531197237/)
   - **Discord**: kaido02

For collaboration, questions about the project, or professional inquiries, feel free to reach out!

## 🔮 Roadmap

- [ ] Mobile application for drivers
- [ ] GPS tracking integration
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] API rate limiting
- [ ] Real-time notifications
- [ ] Automated route optimization
- [ ] Integration with external logistics services

---

**Built with ❤️ for the logistics industry**
