from app import db
from datetime import datetime
import json

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # One-to-many relationship with conversations
    conversations = db.relationship('Conversation', backref='user', lazy='dynamic')
    
    # One-to-one relationship with settings
    settings = db.relationship('UserSettings', backref='user', uselist=False)
    
    # Flask-Login compatibility methods
    def is_authenticated(self):
        return True
        
    def is_active(self):
        return True
        
    def is_anonymous(self):
        return False
        
    def get_id(self):
        return str(self.id)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(100), default="New Conversation")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # One-to-many relationship with messages
    messages = db.relationship('Message', backref='conversation', lazy='dynamic')
    
    def __repr__(self):
        return f'<Conversation {self.id} - {self.title}>'

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'))
    is_user = db.Column(db.Boolean, default=True)  # True if from user, False if from AI
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        sender = "User" if self.is_user else "AI"
        return f'<Message {self.id} from {sender}>'

class UserSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    
    # AI safety and ethics settings (all default to True for safety)
    content_filter_enabled = db.Column(db.Boolean, default=True)
    ethics_check_enabled = db.Column(db.Boolean, default=True)
    permission_required = db.Column(db.Boolean, default=True)
    
    # Model preferences
    preferred_model = db.Column(db.String(100), default="gpt2")
    
    # Advanced settings stored as JSON
    advanced_settings = db.Column(db.Text, default='{}')
    
    def get_advanced_settings(self):
        """Parse and return advanced settings as a dictionary"""
        try:
            return json.loads(self.advanced_settings)
        except:
            return {}
    
    def set_advanced_settings(self, settings_dict):
        """Convert dictionary to JSON and store"""
        self.advanced_settings = json.dumps(settings_dict)
    
    def __repr__(self):
        return f'<UserSettings for user_id {self.user_id}>'

class ModelCache(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(100), unique=True, nullable=False)
    source_url = db.Column(db.String(255))
    local_path = db.Column(db.String(255))
    downloaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ModelCache {self.model_name}>'
