"""
Flask application factory for Transmission Line Routing Optimization Tool
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS
from config import config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'


def create_app(config_name='default'):
    """
    Application factory pattern

    Args:
        config_name: Configuration to use (development, production, testing)

    Returns:
        Flask application instance
    """
    import os
    # Set template and static folders relative to project root
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    CORS(app)
    
    # Register blueprints
    from app.routes_api import api_bp
    from app.auth import auth_bp
    from app.routes_qgis_api import qgis_api_bp, cost_surface_bp

    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(qgis_api_bp, url_prefix='/api/qgis')
    app.register_blueprint(cost_surface_bp)
    
    # Register main routes
    from app import views
    app.register_blueprint(views.main_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app

