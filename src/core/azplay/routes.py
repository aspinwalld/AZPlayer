from azplay import app, db, bcrypt
from azplay.forms import *
from azplay.models import UsersModel, Categories, Cuts
from flask import render_template, url_for, flash, redirect, request, abort, send_file
from flask_login import login_user, current_user, logout_user, login_required
from flask_user import roles_required
from werkzeug.utils import secure_filename
import os
from azplay.utils.transcode import Transcode

# Initialize transcoding engine
transcoder = Transcode(app.config['UPLOAD_FOLDER'], normalize=True)


def allowed_file(filename):
    UPLOAD_ALLOWED_EXTENSIONS = {'wav', 'mp3'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in UPLOAD_ALLOWED_EXTENSIONS


def noauth():
    return render_template('/error/noauth.j2')


def auth(required_level: int) -> bool:
    '''Check if current user has access to a resource'''
    if current_user.role >= required_level:
        return True
    return False


@app.errorhandler(404)
def page_not_found(e):
    '''Render template on 404 error'''
    return render_template('error/404.j2'), 404


@app.errorhandler(500)
def internal_server_error(e):
    '''Render template on 500 error'''
    return render_template('error/500.j2'), 500


@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    '''Render default / dashboard template'''
    if not auth(1):
        noauth()

    return render_template('dashboard.j2')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = UsersModel.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password.', 'danger')
    return render_template('login.j2', form=form)


@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user = UsersModel(name=form.name.data, email=form.email.data,
                          password=hashed_password, role=0, is_locked=False)
        db.session.add(user)
        db.session.commit()
        flash('Your AZPlay account has been created. Please log in.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('register.j2', form=form)


@app.route('/users')
@login_required
def users():
    if not auth(1):
        noauth()

    users = UsersModel.query.all()
    print(users)
    return render_template('users.j2', users=users)


@app.route('/users/new', methods=['GET', 'POST'])
@login_required
def new_user():
    if not auth(2):
        noauth()

    form = NewUserForm()
    if form.validate_on_submit():
        user = UsersModel(
            name=form.name.data,
            email=form.email.data,
            password=form.password.data,
            role=form.role.data,
        )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('users'))
    return render_template('user-create.j2', form=form)


@app.route('/users/<int:user_id>/update', methods=['GET', 'POST'])
@login_required
def update_user(user_id):
    if not auth(2):
        noauth()

    user = UsersModel.query.get_or_404(user_id)
    form = UpdateUserForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')

        user.name = form.name.data
        user.email = form.email.data
        user.password = hashed_password
        user.role = form.role.data

        db.session.commit()

        return redirect(url_for('users'))

    elif request.method == 'GET':
        form.name.data = user.name
        form.email.data = user.email
        form.role.data = user.role
        form.is_locked.data = user.is_locked

    return render_template('user-edit.j2', form=form)


@app.route('/users/<int:user_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_user(user_id):
    if not auth(2):
        noauth()

    user = UsersModel.query.get_or_404(user_id)

    if current_user == user:
        flash('Please don\'t delete yourself...', 'danger')
        return redirect(url_for('users'))

    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('categories'))


@app.route('/categories')
@login_required
def categories():
    if not auth(1):
        noauth()

    categories = Categories.query.all()
    return render_template('categories.j2', categories=categories)


@app.route('/categories/new', methods=['GET', 'POST'])
@login_required
def new_category():
    if not auth(1):
        noauth()

    form = NewCategoryForm()
    if form.validate_on_submit():
        category = Categories(
            name=form.name.data,
            color=form.color.data
        )
        db.session.add(category)
        db.session.commit()
        return redirect(url_for('categories'))
    return render_template('category-edit.j2', form=form)


@app.route('/categories/<int:category_id>/update', methods=['GET', 'POST'])
@login_required
def update_category(category_id):
    if not auth(1):
        noauth()

    category = Categories.query.get_or_404(category_id)
    form = UpdateCategoryForm()

    if form.validate_on_submit():
        category.name = form.name.data
        category.color = form.color.data

        db.session.commit()

        return redirect(url_for('categories'))

    elif request.method == 'GET':
        form.name.data = category.name
        form.color.data = category.color

    return render_template('category-edit.j2', form=form)


@app.route('/categories/<int:category_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_category(category_id):
    if not auth(2):
        noauth()

    category = Categories.query.get_or_404(category_id)

    if len(category.cuts) > 0:
        flash('Cannot delete categories with cuts assigned.', 'danger')
        return redirect(url_for('categories'))

    db.session.delete(category)
    db.session.commit()
    return redirect(url_for('categories'))


@app.route('/cuts')
@login_required
def cuts():
    if not auth(1):
        noauth()

    cuts = Cuts.query.all()
    return render_template('cuts.j2', cuts=cuts)


@app.route('/cuts/upload', methods=['GET', 'POST'])
@login_required
def upload_cut():
    if not auth(1):
        noauth()

    form = UploadCutAudioForm()

    if form.validate_on_submit():

        if 'file' not in request.files:
            flash('Error uploading audio file.', 'danger')
            return redirect(request.url)
        
        file = request.files['file']

        if file.filename == '':
            # User did not select a file for upload
            flash('Please select an audio file to upload', 'warning')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            transcoder.import_cut(filename, 6969)
            # file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('cuts'))
        
    return render_template('cut-upload.j2', form=form)


@app.route('/cuts/new', methods=['GET', 'POST'])
@login_required
def new_cut():
    if not auth(1):
        noauth()

    categories = Categories.query.all()
    choices = [(category.id, category.name) for category in categories]

    form = NewCutForm()
    form.category.choices = choices

    if form.validate_on_submit():
        cut = Cuts(
            cut=form.cut.data,
            category=form.category.data,
            duration=form.duration.data,
            track_begin=form.track_begin.data,
            track_end=form.track_end.data,
            intro_begin=form.intro_begin.data,
            intro_end=form.intro_end.data,
            segue_begin=form.segue_begin.data,
            segue_end=form.segue_end.data,
            album=form.album.data,
            artist=form.artist.data,
            title=form.title.data,
            topplay=form.topplay.data,
            link_audio=form.link_audio.data
        )
        db.session.add(cut)
        db.session.commit()
        return redirect(url_for('cuts'))
    return render_template('cut-edit.j2', form=form)


@app.route('/cuts/<int:cut_id>/update', methods=['GET', 'POST'])
@login_required
def update_cut(cut_id):
    if not auth(1):
        noauth()

    cut = Cuts.query.get_or_404(cut_id)
    form = UpdateCategoryForm()

    categories = Categories.query.all()
    choices = [(category.id, category.name) for category in categories]
    form.category.choices = choices

    if form.validate_on_submit():
        cut.cut = form.cut.data,
        cut.category = form.category.data,
        cut.duration = form.duration.data,
        cut.track_begin = form.track_begin.data,
        cut.track_end = form.track_end.data,
        cut.intro_begin = form.intro_begin.data,
        cut.intro_end = form.intro_end.data,
        cut.segue_begin = form.segue_begin.data,
        cut.segue_end = form.segue_end.data,
        cut.album = form.album.data,
        cut.artist = form.artist.data,
        cut.title = form.title.data,
        cut.topplay = form.topplay.data,
        cut.link_audio = form.link_audio.data

        db.session.commit()

        return redirect(url_for('categories'))

    elif request.method == 'GET':
        form.cut.data = cut.cut
        form.category.data = cut.category
        form.duration.data = cut.duration
        form.track_begin.data = cut.track_begin
        form.track_end.data = cut.track_end
        form.intro_begin.data = cut.intro_begin
        form.intro_end.data = cut.intro_end
        form.segue_begin.data = cut.segue_begin
        form.segue_end.data = cut.segue_end
        form.album.data = cut.album
        form.artist.data = cut.artist
        form.title.data = cut.title
        form.topplay.data = cut.topplay
        form.link_audio.data = cut.link_audio

    return render_template('cut-edit.j2', form=form)


@app.route('/cuts/<int:cut_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_cut(cut_id):
    if not auth(2):
        noauth()

    cut = Cuts.query.get_or_404(cut_id)

    # @TODO If cut in schedules, no allow deletey

    db.session.delete(cut)
    db.session.commit()
    return redirect(url_for('cuts'))
