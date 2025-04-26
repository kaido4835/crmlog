from datetime import datetime
from sqlalchemy import Enum, JSON, Text
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
    name = db.Column(db.String(128), nullable=False, index=True)
    legal_name = db.Column(db.String(256), nullable=False)
    tax_id = db.Column(db.String(64), nullable=False, unique=True, index=True)
    address = db.Column(db.String(256), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False, index=True)
    website = db.Column(db.String(128), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = db.relationship('CompanyOwner', uselist=False, back_populates='company', cascade='all, delete-orphan')
    managers = db.relationship('Manager', back_populates='company', cascade='all, delete-orphan')
    operators = db.relationship('Operator', back_populates='company', cascade='all, delete-orphan')
    drivers = db.relationship('Driver', back_populates='company', cascade='all, delete-orphan')
    statistics = db.relationship('Statistics', back_populates='company', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Company {self.name}>'


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(Enum(TaskStatus), default=TaskStatus.NEW, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deadline = db.Column(db.DateTime, nullable=True, index=True)

    # Adding company_id to enable more efficient queries by company
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Relationships
    company = db.relationship('Company', foreign_keys=[company_id])
    creator = db.relationship('User', foreign_keys=[creator_id], backref='created_tasks')
    assignee = db.relationship('User', foreign_keys=[assignee_id], backref='assigned_tasks')
    route = db.relationship('Route', uselist=False, back_populates='task', cascade='all, delete-orphan')
    documents = db.relationship('Document', back_populates='task', cascade='all, delete-orphan')
    messages = db.relationship('Message', back_populates='task', cascade='all, delete-orphan')

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
    start_time = db.Column(db.DateTime, nullable=True, index=True)
    end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(Enum(RouteStatus), default=RouteStatus.PLANNED, nullable=False, index=True)

    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=False, index=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False, unique=True)

    # Adding company_id to enable more efficient queries by company
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)

    # Relationships
    company = db.relationship('Company', foreign_keys=[company_id])
    driver = db.relationship('Driver', back_populates='routes')
    task = db.relationship('Task', back_populates='route')

    def __repr__(self):
        return f'<Route {self.id}: {self.start_point} to {self.end_point}>'


class DocumentCategory(enum.Enum):
    PERSONAL = "personal"
    VEHICLE = "vehicle"
    TASK = "task"
    ROUTE = "route"
    OTHER = "other"


class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    file_path = db.Column(db.String(256), nullable=False)
    file_type = db.Column(db.String(64), nullable=False)
    size = db.Column(db.Integer, nullable=False)  # in bytes
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    document_category = db.Column(Enum(DocumentCategory), default=DocumentCategory.OTHER, nullable=False)

    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=True, index=True)
    route_id = db.Column(db.Integer, db.ForeignKey('routes.id'), nullable=True, index=True)
    access_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Adding company_id to enable more efficient queries by company
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)

    # Relationships
    company = db.relationship('Company', foreign_keys=[company_id])
    uploader = db.relationship('User', foreign_keys=[uploader_id], backref='uploaded_documents')
    task = db.relationship('Task', back_populates='documents')
    route = db.relationship('Route', back_populates='documents')
    access_user = db.relationship('User', foreign_keys=[access_user_id], backref='accessible_documents')

    def __repr__(self):
        return f'<Document {self.title}>'


class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    is_read = db.Column(db.Boolean, default=False, index=True)

    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=True, index=True)

    # Adding company_id to enable more efficient queries by company
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)

    # Relationships
    company = db.relationship('Company', foreign_keys=[company_id])
    sender = db.relationship('User', foreign_keys=[sender_id], back_populates='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], back_populates='received_messages')
    task = db.relationship('Task', back_populates='messages')

    def __repr__(self):
        return f'<Message {self.id}>'


class Log(db.Model):
    __tablename__ = 'logs'

    id = db.Column(db.Integer, primary_key=True)
    action_type = db.Column(Enum(ActionType), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    ip_address = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(256), nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    # Adding company_id to enable more efficient queries by company
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True, index=True)

    # Relationships
    company = db.relationship('Company', foreign_keys=[company_id])
    user = db.relationship('User', back_populates='logs')

    def __repr__(self):
        return f'<Log {self.id}: {self.action_type.value}>'


class Statistics(db.Model):
    __tablename__ = 'statistics'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    metrics = db.Column(JSON, nullable=False)
    period_start = db.Column(db.DateTime, nullable=False, index=True)
    period_end = db.Column(db.DateTime, nullable=False, index=True)
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    company = db.relationship('Company', back_populates='statistics')
    user = db.relationship('User', backref='statistics')

    def __repr__(self):
        return f'<Statistics {self.id}>'