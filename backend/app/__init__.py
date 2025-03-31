from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config

db = SQLAlchemy()
jwt = JWTManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    CORS(app)

    # Register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from app.security import bp as security_bp
    app.register_blueprint(security_bp, url_prefix='/api/security')

    from app.applications import bp as applications_bp
    app.register_blueprint(applications_bp, url_prefix='/api/applications')

    return app 