from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange
from azplay.models import Users, Categories, Cuts


# Registration form used for new user self-signup.
class RegisterForm(FlaskForm):
    name = StringField('Full Name',
                       validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Create Account')

    def validate_username(self, username):
        user = Users.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(
                'Username unavailable. Please choose a different one or log in.')

    def validate_email(self, email):
        user = Users.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(
                'Email unavailable. Please choose a different one or log in.')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password',
                             validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


# Admin user management - update existing users
class UpdateUserForm(FlaskForm):
    name = StringField('Full Name',
                       validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField('NEP Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField(
        'New Password (Leave blank for unchanged)', validators=[Length(min=8, max=64)])
    role = SelectField('Role', choices=[(0, 'Viewer'), (1, 'Operator'), (
        2, 'Admin')], validators=[DataRequired()])
    is_locked = BooleanField('Lock User')
    submit = SubmitField('Update Account')


# Admin user management - create new users
class NewUserForm(FlaskForm):
    name = StringField('Full Name',
                       validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField('NEP Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[[(0, 'Viewer'), (1, 'Operator'), (
        2, 'Admin')]])
    submit = SubmitField('Create User')

    def validate_username(self, username):
        user = Users.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(
                'Username unavailable. Please choose a different one or log in.')

    def validate_email(self, email):
        user = Users.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(
                'Email unavailable. Please choose a different one or log in.')


class NewCategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[
                       DataRequired(), Length(min=1, max=32)])
    color = StringField('Color', validators=[
                        DataRequired(), Length(min=7, max=7)])
    submit = SubmitField('Create Category')

    def validate_name(self, name):
        category = Categories.query.filter_by(name=name.data).first()
        if category:
            raise ValidationError('Category name already in use.')


class UpdateCategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[
                       DataRequired(), Length(min=1, max=32)])
    color = StringField('Color', validators=[
                        DataRequired(), Length(min=7, max=7)])
    submit = SubmitField('Update Category')


class NewCutForm(FlaskForm):
    cut = IntegerField('Cut ID', validators=[
                       DataRequired(), NumberRange(min=0, max=999_999)])
    category = SelectField('Category', validators=[DataRequired()])
    duration = IntegerField('Duration', validators=[
                            DataRequired(), NumberRange(min=0)])
    track_begin = IntegerField('Track Start', validators=[
                               DataRequired(), NumberRange(min=0)])
    track_end = IntegerField('Track End', validators=[
                             DataRequired(), NumberRange(min=0)])
    intro_begin = IntegerField('Intro Start', validators=[NumberRange(min=0)])
    intro_end = IntegerField('Intro End', validators=[NumberRange(min=0)])
    segue_begin = IntegerField('Segue Start', validators=[NumberRange(min=0)])
    segue_end = IntegerField('Segue End', validators=[NumberRange(min=0)])
    album = StringField('Album')
    artist = StringField('Artist', validators=[DataRequired()])
    title = StringField('Title', validators=[DataRequired()])
    topplay = SelectField('TopPlay', choices=[(0, 'Off'), (1, 'AutoIntro'),
                                              (2, 'AutoPost')])
    link_audio = FileField('WAV File', validators=[DataRequired()])
    submit = SubmitField('Save Cut')

class UploadCutAudioForm(FlaskForm):
    cut = IntegerField('Cut ID', validators=[DataRequired(), NumberRange(min=0, max=999_999)])
    audio = FileField('WAV File')
    submit = SubmitField('Upload')
