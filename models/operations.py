from datetime import datetime
from sqlalchemy import Enum, JSON
import enum

from app import db


class TaskStatus(enum.Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RouteStatus(enum.Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ActionType(enum.Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    DOWNLOAD = "download"
    UPLOAD = "upload"
    ASSIGN = "assign"


class Company(db.Model):
    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    legal_name = db.Column(db.String(256), nullable=False)
    tax_id = db.Column(db.String(64), nullable=False)
    address = db.Column(db.String(256), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    website = db.Column(db.String(128), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = db.relationship('CompanyOwner', uselist=False, back_populates='company')
    managers = db.relationship('Manager', back_populates='company')
    operators = db.relationship('Operator', back_populates='company')
    drivers = db.relationship('Driver', back_populates='company')
    statistics = db.relationship('Statistics', back_populates='company')

    def __repr__(self):
        return f'<Company {self.name}>'


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(Enum(TaskStatus), default=TaskStatus.NEW, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deadline = db.Column(db.DateTime, nullable=True)

    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Relationships
    creator = db.relationship('User', foreign_keys=[creator_id], backref='created_tasks')
    assignee = db.relationship('User', foreign_keys=[assignee_id], backref='assigned_tasks')
    route = db.relationship('Route', uselist=False, back_populates='task')
    documents = db.relationship('Document', back_populates='task')
    messages = db.relationship('Message', back_populates='task')

    def __repr__(self):
        return f'<Task {self.title}>'


class Route(db.Model):
    __tablename__ = 'routes'

    id = db.Column(db.Integer, primary_key=True)
    start_point = db.Column(db.String(256), nullable=False)
    end_point = db.Column(db.String(256), nullable=False)
    waypoints = db.Column(JSON, nullable=True)
    distance = db.Column(db.Float, nullable=True)
    estimated_time = db.Column(db.Integer, nullable=True)  # in minutes
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(Enum(RouteStatus), default=RouteStatus.PLANNED, nullable=False)

    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)

    # Relationships
    driver = db.relationship('Driver', back_populates='routes')
    task = db.relationship('Task', back_populates='route')

    def __repr__(self):
        return f'<Route {self.id}: {self.start_point} to {self.end_point}>'


class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    file_path = db.Column(db.String(256), nullable=False)
    file_type = db.Column(db.String(64), nullable=False)
    size = db.Column(db.Integer, nullable=False)  # in bytes
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)

    # Relationships
    uploader = db.relationship('User', backref='uploaded_documents')
    task = db.relationship('Task', back_populates='documents')

    def __repr__(self):
        return f'<Document {self.title}>'


class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=True)

    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], back_populates='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], back_populates='received_messages')
    task = db.relationship('Task', back_populates='messages')

    def __repr__(self):
        return f'<Message {self.id}>'


class Log(db.Model):
    __tablename__ = 'logs'

    id = db.Column(db.Integer, primary_key=True)
    action_type = db.Column(Enum(ActionType), nullable=False)
    description = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(256), nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationships
    user = db.relationship('User', back_populates='logs')

    def __repr__(self):
        return f'<Log {self.id}: {self.action_type.value}>'


class Statistics(db.Model):
    __tablename__ = 'statistics'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    metrics = db.Column(JSON, nullable=False)
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    company = db.relationship('Company', back_populates='statistics')
    user = db.relationship('User', backref='statistics')

    def __repr__(self):
        return f'<Statistics {self.id}>'