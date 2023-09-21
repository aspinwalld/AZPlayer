import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

load_dotenv()

DEBUG = bool(os.environ.get('DEBUG', False))
SECRET = os.environ.get('SECRET', 'guest')
UPLOAD_FOLDER = os.environ.get('SNDDIR')

app = Flask(__name__)

app.config['SECRET_KEY'] = SECRET
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///azplay.db'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'primary'

from azplay import routes