from azplay import app, db, login_manager
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return UsersModel.query.get(int(user_id))


# Database table for WITS Users
class UsersModel(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)
    role = db.Column(db.Integer, nullable=False, default=1)
    is_locked = db.Column(db.Boolean)


class Categories(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)
    color = db.Column(db.String(7))
    cuts = db.relationship('Cuts', backref='categories', lazy=True)


class Cuts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cut = db.Column(db.Integer, unique=True, nullable=False)
    category = db.Column(db.Integer, db.ForeignKey(
        'categories.id'), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    track_begin = db.Column(db.Integer, nullable=False)
    track_end = db.Column(db.Integer, nullable=False)
    intro_begin = db.Column(db.Integer)
    intro_end = db.Column(db.Integer)
    segue_begin = db.Column(db.Integer)
    segue_end = db.Column(db.Integer)
    album = db.Column(db.String(64))
    artist = db.Column(db.String(64), nullable=False)
    title = db.Column(db.String(64), nullable=False)
    topplay = db.Column(db.Integer)
    link_audio = db.Column(db.String(255))


with app.app_context():
    db.create_all()
