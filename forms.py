from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, BooleanField, SubmitField,
    SelectField, TextAreaField, FileField, DateTimeField,
    IntegerField, FloatField
)
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length,
    ValidationError, Optional, Regexp
)
from flask_wtf.file import FileAllowed

from models import User, UserRole


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')


class RequestPasswordResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if not user:
            raise ValidationError('There is no account with that email. You must register first.')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message="Password must be at least 8 characters long")
    ])
    password2 = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Reset Password')


class UserForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=64),
        Regexp('^[A-Za-z0-9_.]+$', message='Username can only contain letters, numbers, dots and underscores')
    ])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message="Password must be at least 8 characters long")
    ])
    password2 = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=64)])
    phone = StringField('Phone', validators=[Length(max=20)])
    role = SelectField('Role', validators=[DataRequired()], choices=[
        (UserRole.ADMIN.value, 'Administrator'),
        (UserRole.COMPANY_OWNER.value, 'Company Owner'),
        (UserRole.MANAGER.value, 'Manager'),
        (UserRole.OPERATOR.value, 'Operator'),
        (UserRole.DRIVER.value, 'Driver')
    ])
    is_active = BooleanField('Active Account', default=True)
    profile_image = FileField('Profile Image', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])
    submit = SubmitField('Create User')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already in use. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')


class EditUserForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=64),
        Regexp('^[A-Za-z0-9_.]+$', message='Username can only contain letters, numbers, dots and underscores')
    ])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=64)])
    phone = StringField('Phone', validators=[Length(max=20)])
    role = SelectField('Role', validators=[DataRequired()])
    is_active = BooleanField('Active Account', default=True)
    profile_image = FileField('Profile Image', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])
    submit = SubmitField('Update User')

    def __init__(self, original_username, original_email, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email
        self.role.choices = [
            (UserRole.ADMIN.value, 'Administrator'),
            (UserRole.COMPANY_OWNER.value, 'Company Owner'),
            (UserRole.MANAGER.value, 'Manager'),
            (UserRole.OPERATOR.value, 'Operator'),
            (UserRole.DRIVER.value, 'Driver')
        ]

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username already in use. Please choose a different one.')

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email already registered. Please use a different one.')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message="Password must be at least 8 characters long")
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match')
    ])
    submit = SubmitField('Change Password')


class AdminRegistrationForm(UserForm):
    admin_level = IntegerField('Admin Level', default=1, validators=[DataRequired()])
    submit = SubmitField('Create Admin')


class CompanyForm(FlaskForm):
    name = StringField('Company Name', validators=[DataRequired(), Length(max=128)])
    legal_name = StringField('Legal Name', validators=[DataRequired(), Length(max=256)])
    tax_id = StringField('Tax ID', validators=[DataRequired(), Length(max=64)])
    address = StringField('Address', validators=[DataRequired(), Length(max=256)])
    phone = StringField('Phone', validators=[DataRequired(), Length(max=20)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    website = StringField('Website', validators=[Optional(), Length(max=128)])
    submit = SubmitField('Save Company')


class CompanyOwnerRegistrationForm(UserForm):
    company_id = SelectField('Company', coerce=int, validators=[Optional()])
    create_new_company = BooleanField('Create New Company')

    # Company fields (for new company creation)
    company_name = StringField('Company Name', validators=[Optional(), Length(max=128)])
    company_legal_name = StringField('Legal Name', validators=[Optional(), Length(max=256)])
    company_tax_id = StringField('Tax ID', validators=[Optional(), Length(max=64)])
    company_address = StringField('Address', validators=[Optional(), Length(max=256)])
    company_phone = StringField('Company Phone', validators=[Optional(), Length(max=20)])
    company_email = StringField('Company Email', validators=[Optional(), Email(), Length(max=120)])
    company_website = StringField('Company Website', validators=[Optional(), Length(max=128)])

    submit = SubmitField('Create Company Owner')

    def __init__(self, *args, **kwargs):
        super(CompanyOwnerRegistrationForm, self).__init__(*args, **kwargs)
        self.role.data = UserRole.COMPANY_OWNER.value

    def validate(self):
        if not super(CompanyOwnerRegistrationForm, self).validate():
            return False

        if not self.company_id.data and not self.create_new_company.data:
            self.company_id.errors.append('Please select a company or create a new one')
            return False

        if self.create_new_company.data:
            if not self.company_name.data:
                self.company_name.errors.append('Company name is required')
                return False
            if not self.company_legal_name.data:
                self.company_legal_name.errors.append('Company legal name is required')
                return False
            if not self.company_tax_id.data:
                self.company_tax_id.errors.append('Company tax ID is required')
                return False
            if not self.company_address.data:
                self.company_address.errors.append('Company address is required')
                return False
            if not self.company_phone.data:
                self.company_phone.errors.append('Company phone is required')
                return False
            if not self.company_email.data:
                self.company_email.errors.append('Company email is required')
                return False

        return True


class SearchForm(FlaskForm):
    search = StringField('Search', validators=[DataRequired()])
    submit = SubmitField('Search')