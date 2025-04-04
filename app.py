import os
import logging
import re
import html

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with Base class
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login_test'

# Initialize CSRF Protection but don't enable it for now
csrf = CSRFProtect()
# Temporarily disable CSRF protection to debug login issues
# csrf.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Add custom Jinja filters
@app.template_filter('nl2br')
def nl2br_filter(s):
    """Convert newlines to <br> tags for HTML display"""
    if s is None:
        return ""
    # Replace newlines with <br> tags
    return s.replace('\n', '<br>')

# Configure the SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///ai_system.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the app with the extension
db.init_app(app)

# Import and register routes
with app.app_context():
    # Import models here to avoid circular imports
    import models
    from routes import register_routes
    from auth import auth_bp
    
    # Register the routes to the app
    register_routes(app)
    
    # Register the auth blueprint
    app.register_blueprint(auth_bp)
    
    # Create database tables if they don't exist
    db.create_all()

    logger.info("Database initialized and tables created")
