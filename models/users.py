from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import Enum
import enum

from app import db


class UserRole(enum.Enum):
    ADMIN = "ADMIN"
    COMPANY_OWNER = "COMPANY_OWNER"
    MANAGER = "MANAGER"
    OPERATOR = "OPERATOR"
    DRIVER = "DRIVER"


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    profile_image = db.Column(db.String(256), nullable=True)
    role = db.Column(Enum(UserRole), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    # Relationships
    admin = db.relationship('Admin', uselist=False, back_populates='user', cascade='all, delete-orphan')
    company_owner = db.relationship('CompanyOwner', uselist=False, back_populates='user', cascade='all, delete-orphan')
    manager = db.relationship('Manager', uselist=False, back_populates='user', cascade='all, delete-orphan')
    operator = db.relationship('Operator', uselist=False, back_populates='user', cascade='all, delete-orphan')
    driver = db.relationship('Driver', uselist=False, back_populates='user', cascade='all, delete-orphan')

    logs = db.relationship('Log', back_populates='user', cascade='all, delete-orphan')
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', back_populates='sender', cascade='all, delete-orphan')
    received_messages = db.relationship('Message', foreign_keys='Message.recipient_id', back_populates='recipient', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f'<User {self.username}>'


class Admin(db.Model):
    __tablename__ = 'admins'

    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    admin_level = db.Column(db.Integer, default=1)  # Higher level means more privileges

    user = db.relationship('User', back_populates='admin')

    def __repr__(self):
        return f'<Admin {self.user.username}>'


class CompanyOwner(db.Model):
    __tablename__ = 'company_owners'

    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))

    user = db.relationship('User', back_populates='company_owner')
    company = db.relationship('Company', back_populates='owner')

    def __repr__(self):
        return f'<CompanyOwner {self.user.username}>'


class Manager(db.Model):
    __tablename__ = 'managers'

    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))

    user = db.relationship('User', back_populates='manager')
    company = db.relationship('Company', back_populates='managers')
    operators = db.relationship('Operator', back_populates='manager')

    def __repr__(self):
        return f'<Manager {self.user.username}>'


class Operator(db.Model):
    __tablename__ = 'operators'

    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('managers.id'))
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))

    user = db.relationship('User', back_populates='operator')
    manager = db.relationship('Manager', back_populates='operators')
    company = db.relationship('Company', back_populates='operators')
    drivers = db.relationship('Driver', back_populates='operator')

    def __repr__(self):
        return f'<Operator {self.user.username}>'


class Driver(db.Model):
    __tablename__ = 'drivers'

    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    operator_id = db.Column(db.Integer, db.ForeignKey('operators.id'))
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
    license_number = db.Column(db.String(64), nullable=False)
    vehicle_info = db.Column(db.String(256), nullable=False)

    user = db.relationship('User', back_populates='driver')
    operator = db.relationship('Operator', back_populates='drivers')
    company = db.relationship('Company', back_populates='drivers')
    routes = db.relationship('Route', back_populates='driver')

    def __repr__(self):
        return f'<Driver {self.user.username}>'