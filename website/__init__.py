from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from flask_login import LoginManager
from flask_session import Session
import logging


db = SQLAlchemy()
DB_NAME = 'database.db'


def create_app(mode):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dahdahoda'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    app.config['SECRET_KEY'] = 'hard to guess string'
    # socketio = SocketIO(app)
    log = logging.getLogger('werkzeug')
    log.disabled = True

    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_TYPE"] = "filesystem"
    Session(app)
    from .models import User, UserInteraction
    create_db(app)

    from .web_base import web_base
    app.register_blueprint(web_base, url_prefix='/')
    login_manager = LoginManager()
    login_manager.login_view = 'web_base.login'

    if mode == 'u2u':
        from .web_u2u import web_u2u
        app.register_blueprint(web_u2u, url_prefix='/u2u')
        login_manager.init_app(app)

    else:
        from .web_u2m import web_u2m
        app.register_blueprint(web_u2m, url_prefix='/u2m')
        login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app


def create_db(app):
    if not os.path.exists('instance/{}'.format(DB_NAME)):
        with app.app_context():
            db.create_all()
