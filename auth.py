import logging
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from models import User, UserSettings

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login_test', methods=['GET', 'POST'])
def login_test():
    """Render test login page and handle form submissions"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    from forms import LoginForm, RegistrationForm
    login_form = LoginForm()
    registration_form = RegistrationForm()
    
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        
        if form_type == 'login' and login_form.validate_on_submit():
            user = User.query.filter_by(username=login_form.username.data).first()
            if user and check_password_hash(user.password_hash, login_form.password.data):
                login_user(user)
                flash('Logged in successfully!', 'success')
                return redirect(url_for('index'))
            flash('Invalid username or password', 'danger')
            
        elif form_type == 'register' and registration_form.validate_on_submit():
            return redirect(url_for('auth.register'))
    
    return render_template('login_test.html', 
                         login_form=login_form,
                         registration_form=registration_form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if current_user.is_authenticated:
        logger.debug("User already authenticated, redirecting to index")
        return redirect(url_for('index'))
    
    logger.debug(f"Login route accessed with method: {request.method}")
    logger.debug(f"Request form data: {request.form}")
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        logger.debug(f"Login attempt for user: {username}")
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            # Login user with Flask-Login
            login_user(user)
            logger.debug(f"User {username} logged in successfully")
            flash('Logged in successfully!', 'success')
            
            # Redirect to the next page or index
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            logger.debug(f"Login failed for user: {username}")
            flash('Invalid username or password', 'danger')
    
    return redirect(url_for('auth.login_test'))

@auth_bp.route('/register', methods=['POST'])
def register():
    """Handle user registration"""
    if current_user.is_authenticated:
        flash('You are already logged in', 'info')
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        logger.debug(f"Registration attempt for user: {username}, email: {email}")
        
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            return redirect(url_for('auth.login_test'))
        
        # Check if username or email already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        
        if existing_user:
            flash('Username or email already exists', 'danger')
            return redirect(url_for('auth.login_test'))
        
        # Create new user
        password_hash = generate_password_hash(password)
        new_user = User(username=username, email=email, password_hash=password_hash)
        
        # Add user to database
        db.session.add(new_user)
        db.session.commit()
        
        # Create default settings for user
        settings = UserSettings(user_id=new_user.id)
        db.session.add(settings)
        db.session.commit()
        
        logger.debug(f"User {username} registered successfully")
        
        # Log user in
        login_user(new_user)
        flash('Registration successful!', 'success')
        
        return redirect(url_for('index'))
    
    return redirect(url_for('auth.login_test'))

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))