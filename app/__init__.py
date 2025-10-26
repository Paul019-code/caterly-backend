# app/__init__.py
from flask import Flask
from config import Config
from .extensions import db, migrate, jwt, cors


def create_app(config_class=None):
    app = Flask(__name__, static_folder=None)
    app.config.from_object(config_class or Config)

    # initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app)

    # register Blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.menu_routes import menu_bp
    from app.routes.order_routes import order_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(menu_bp, url_prefix='/api/menu')
    app.register_blueprint(order_bp, url_prefix='/api/order')

    return app
