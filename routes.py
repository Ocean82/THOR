import os
import logging
from flask import render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import json

from app import db
from models import User, Conversation, Message, UserSettings, ModelCache
from ai_engine import AIEngine
from model_integrator import ModelIntegrator

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize AI components
ai_engine = AIEngine()
model_integrator = ModelIntegrator()

def register_routes(app):
    
    @app.route('/test_openai')
    def test_openai():
        try:
            # Attempt to use the OpenAI integration
            result = ai_engine.generate_response("Hello, this is a test of the OpenAI API integration. Please respond with a confirmation.")
            return jsonify({"status": "success", "message": "OpenAI API is working!", "response": result})
        except Exception as e:
            return jsonify({"status": "error", "message": f"OpenAI API error: {str(e)}"})
            
    """Register all routes with the Flask app"""
    
    @app.route('/')
    def index():
        """Render the main page"""
        # Check if user is logged in
        user_id = session.get('user_id')
        
        if user_id:
            # Get user data
            user = User.query.get(user_id)
            
            # Get conversation history
            conversations = Conversation.query.filter_by(user_id=user_id).order_by(Conversation.created_at.desc()).all()
            
            # Get user settings
            settings = UserSettings.query.filter_by(user_id=user_id).first()
            
            if not settings:
                # Create default settings if none exist
                settings = UserSettings(user_id=user_id)
                db.session.add(settings)
                db.session.commit()
            
            return render_template('index.html', 
                                  user=user, 
                                  conversations=conversations,
                                  settings=settings)
        else:
            # Show welcome page for non-logged-in users
            return render_template('index.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Handle user login"""
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            user = User.query.filter_by(username=username).first()
            
            if user and check_password_hash(user.password_hash, password):
                # Set user session
                session['user_id'] = user.id
                flash('Logged in successfully!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password', 'error')
        
        return render_template('index.html', show_login=True)
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """Handle user registration"""
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            
            # Check if username or email already exists
            existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
            
            if existing_user:
                flash('Username or email already exists', 'error')
                return redirect(url_for('register'))
            
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
            
            # Log user in
            session['user_id'] = new_user.id
            flash('Registration successful!', 'success')
            
            return redirect(url_for('index'))
        
        return render_template('index.html', show_register=True)
    
    @app.route('/logout')
    def logout():
        """Handle user logout"""
        session.pop('user_id', None)
        flash('Logged out successfully', 'success')
        return redirect(url_for('index'))
    
    @app.route('/api/chat', methods=['POST'])
    def chat():
        """API endpoint for chat interactions"""
        data = request.json
        message = data.get('message', '')
        conversation_id = data.get('conversation_id')
        
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({
                'error': 'User not logged in',
                'response': 'Please log in to continue the conversation.'
            }), 401
        
        # Get user settings
        settings = UserSettings.query.filter_by(user_id=user_id).first()
        if not settings:
            settings = UserSettings(user_id=user_id)
            db.session.add(settings)
            db.session.commit()
        
        # Create settings dict for AI engine
        settings_dict = {
            'content_filter_enabled': settings.content_filter_enabled,
            'ethics_check_enabled': settings.ethics_check_enabled,
            'permission_required': settings.permission_required,
            'preferred_model': settings.preferred_model,
            'max_length': 150,  # Default response length
            'temperature': 0.7
        }
        
        # Get or create conversation
        if conversation_id:
            conversation = Conversation.query.get(conversation_id)
            if not conversation or conversation.user_id != user_id:
                return jsonify({'error': 'Invalid conversation ID'}), 400
        else:
            # Create new conversation
            conversation = Conversation(user_id=user_id, title="New Conversation")
            db.session.add(conversation)
            db.session.commit()
            conversation_id = conversation.id
        
        # Add user message to database
        user_message = Message(
            conversation_id=conversation_id,
            is_user=True,
            content=message
        )
        db.session.add(user_message)
        db.session.commit()
        
        # Get conversation history
        history = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.timestamp).all()
        conversation_history = [
            {'is_user': msg.is_user, 'content': msg.content}
            for msg in history[-10:]  # Get last 10 messages
        ]
        
        # Generate AI response
        response_data = ai_engine.generate_response(
            message, 
            conversation_history=conversation_history,
            settings=settings_dict
        )
        
        # Check if this requires permission
        if response_data.get('requires_permission', False):
            return jsonify({
                'response': response_data['text'],
                'requires_permission': True,
                'permission_reason': response_data.get('permission_reason', ''),
                'conversation_id': conversation_id
            })
        
        # Save AI response to database
        ai_message = Message(
            conversation_id=conversation_id,
            is_user=False,
            content=response_data['text']
        )
        db.session.add(ai_message)
        
        # Update conversation title if it's a new conversation
        if conversation.title == "New Conversation" and len(history) <= 2:
            # Generate a title based on the first message
            if len(message) > 30:
                conversation.title = message[:30] + "..."
            else:
                conversation.title = message
            
        db.session.commit()
        
        return jsonify({
            'response': response_data['text'],
            'conversation_id': conversation_id
        })
    
    @app.route('/api/permission', methods=['POST'])
    def handle_permission():
        """Handle permission requests for restricted operations"""
        data = request.json
        permission_granted = data.get('permission_granted', False)
        operation = data.get('operation', '')
        conversation_id = data.get('conversation_id')
        
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User not logged in'}), 401
        
        if permission_granted:
            # Get user settings and temporarily disable permission requirement
            settings = UserSettings.query.filter_by(user_id=user_id).first()
            
            if settings:
                # Create a temporary settings dict with permission requirements disabled
                settings_dict = {
                    'content_filter_enabled': settings.content_filter_enabled,
                    'ethics_check_enabled': settings.ethics_check_enabled,
                    'permission_required': False,  # Temporarily disable
                    'preferred_model': settings.preferred_model
                }
                
                # Get the last user message from this conversation
                last_message = Message.query.filter_by(
                    conversation_id=conversation_id,
                    is_user=True
                ).order_by(Message.timestamp.desc()).first()
                
                if last_message:
                    # Get conversation history
                    history = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.timestamp).all()
                    conversation_history = [
                        {'is_user': msg.is_user, 'content': msg.content}
                        for msg in history[-10:]
                    ]
                    
                    # Process with permission granted
                    response_data = ai_engine.generate_response(
                        last_message.content,
                        conversation_history=conversation_history,
                        settings=settings_dict
                    )
                    
                    # Save AI response
                    ai_message = Message(
                        conversation_id=conversation_id,
                        is_user=False,
                        content=response_data['text']
                    )
                    db.session.add(ai_message)
                    db.session.commit()
                    
                    return jsonify({
                        'response': response_data['text'],
                        'conversation_id': conversation_id
                    })
            
            return jsonify({
                'error': 'Failed to process with permission',
                'conversation_id': conversation_id
            })
        else:
            # Permission denied
            ai_message = Message(
                conversation_id=conversation_id,
                is_user=False,
                content="Permission denied. I'll continue with standard operations only."
            )
            db.session.add(ai_message)
            db.session.commit()
            
            return jsonify({
                'response': "Permission denied. I'll continue with standard operations only.",
                'conversation_id': conversation_id
            })
    
    @app.route('/settings', methods=['GET', 'POST'])
    def settings():
        """Handle user settings page"""
        user_id = session.get('user_id')
        
        if not user_id:
            flash('Please log in to access settings', 'error')
            return redirect(url_for('index'))
        
        user = User.query.get(user_id)
        user_settings = UserSettings.query.filter_by(user_id=user_id).first()
        
        if not user_settings:
            user_settings = UserSettings(user_id=user_id)
            db.session.add(user_settings)
            db.session.commit()
        
        if request.method == 'POST':
            # Update settings
            user_settings.content_filter_enabled = 'content_filter' in request.form
            user_settings.ethics_check_enabled = 'ethics_check' in request.form
            user_settings.permission_required = 'permission_required' in request.form
            user_settings.preferred_model = request.form.get('preferred_model', 'gpt2')
            
            # Update advanced settings if provided
            advanced_settings = request.form.get('advanced_settings', '{}')
            try:
                # Validate JSON
                json_settings = json.loads(advanced_settings)
                user_settings.set_advanced_settings(json_settings)
            except json.JSONDecodeError:
                flash('Invalid JSON in advanced settings', 'error')
            
            db.session.commit()
            flash('Settings updated successfully', 'success')
        
        # Get available models for the dropdown
        available_models = model_integrator.list_available_models()
        cached_models = model_integrator.list_available_models(source="cached")
        
        return render_template('settings.html', 
                             user=user, 
                             settings=user_settings,
                             available_models=available_models,
                             cached_models=cached_models)
    
    @app.route('/api/models/download', methods=['POST'])
    def download_model():
        """API endpoint to download a model"""
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User not logged in'}), 401
        
        data = request.json
        model_name = data.get('model_name')
        source = data.get('source', 'huggingface')
        
        if not model_name:
            return jsonify({'error': 'Model name is required'}), 400
        
        try:
            if source == 'huggingface':
                # Get the optional HuggingFace token if provided
                hf_token = data.get('hf_token')
                
                # Download from HuggingFace using our new implementation
                model_path = model_integrator.download_from_huggingface(
                    model_id=model_name,
                    model_name=None,  # Use default name based on model_id
                    token=hf_token
                )
                
                if not model_path:
                    return jsonify({
                        'error': 'Failed to download model from HuggingFace'
                    }), 500
                
                # Record in database
                model_cache = ModelCache(
                    model_name=model_name,
                    source_url=f"https://huggingface.co/{model_name}",
                    local_path=model_path
                )
                db.session.add(model_cache)
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': f'Model {model_name} downloaded successfully from HuggingFace',
                    'model_path': model_path
                })
                
            elif source == 'github':
                repo_url = data.get('repo_url')
                if not repo_url:
                    return jsonify({'error': 'Repository URL is required'}), 400
                
                # Get optional GitHub parameters
                branch = data.get('branch', 'main')
                github_token = data.get('github_token')
                
                # Download from GitHub using our new implementation
                model_path = model_integrator.download_from_github(
                    repo_url=repo_url, 
                    model_name=model_name,
                    branch=branch,
                    token=github_token
                )
                
                if model_path:
                    # Record in database
                    model_cache = ModelCache(
                        model_name=model_name,
                        source_url=repo_url,
                        local_path=model_path
                    )
                    db.session.add(model_cache)
                    db.session.commit()
                    
                    return jsonify({
                        'success': True,
                        'message': f'Model {model_name} downloaded from GitHub successfully',
                        'model_path': model_path
                    })
                else:
                    return jsonify({
                        'error': 'Failed to download model from GitHub'
                    }), 500
            else:
                return jsonify({'error': 'Invalid source'}), 400
                
        except Exception as e:
            logger.error(f"Error downloading model: {e}")
            return jsonify({
                'error': f'Error downloading model: {str(e)}'
            }), 500
    
    @app.route('/api/models/clone', methods=['POST'])
    def clone_model():
        """API endpoint to clone and modify a model"""
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User not logged in'}), 401
        
        data = request.json
        original_model = data.get('original_model')
        new_model_name = data.get('new_model_name')
        modifications = data.get('modifications', {})
        
        if not original_model or not new_model_name:
            return jsonify({'error': 'Original model and new model name are required'}), 400
        
        try:
            new_model_path = model_integrator.create_model_clone(
                original_model,
                new_model_name,
                modifications
            )
            
            if new_model_path:
                # Record in database
                model_cache = ModelCache(
                    model_name=new_model_name,
                    source_url=f"cloned from {original_model}",
                    local_path=new_model_path
                )
                db.session.add(model_cache)
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': f'Model {original_model} cloned to {new_model_name} successfully',
                    'model_path': new_model_path
                })
            else:
                return jsonify({
                    'error': 'Failed to clone model'
                }), 500
                
        except Exception as e:
            logger.error(f"Error cloning model: {e}")
            return jsonify({
                'error': f'Error cloning model: {str(e)}'
            }), 500
    
    @app.route('/api/models/list', methods=['GET'])
    def list_models():
        """API endpoint to list available models"""
        source = request.args.get('source', 'all')
        
        try:
            if source == 'huggingface' or source == 'all':
                huggingface_models = model_integrator.list_available_models(source="huggingface")
            else:
                huggingface_models = []
                
            if source == 'cached' or source == 'all':
                cached_models = model_integrator.list_available_models(source="cached")
            else:
                cached_models = []
                
            if source == 'database' or source == 'all':
                db_models = [
                    {
                        "name": model.model_name,
                        "path": model.local_path,
                        "source": "database",
                        "downloaded_at": model.downloaded_at.isoformat() if model.downloaded_at else None
                    }
                    for model in ModelCache.query.all()
                ]
            else:
                db_models = []
            
            # Combine results
            all_models = huggingface_models + cached_models + db_models
            
            return jsonify({
                'models': all_models
            })
            
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return jsonify({
                'error': f'Error listing models: {str(e)}'
            }), 500
    
    @app.route('/conversations', methods=['GET'])
    def view_conversations():
        """View conversation history"""
        user_id = session.get('user_id')
        
        if not user_id:
            flash('Please log in to view conversations', 'error')
            return redirect(url_for('index'))
        
        user = User.query.get(user_id)
        conversations = Conversation.query.filter_by(user_id=user_id).order_by(Conversation.created_at.desc()).all()
        
        return render_template('index.html', 
                             user=user, 
                             conversations=conversations,
                             show_conversations=True)
    
    @app.route('/conversation/<int:conversation_id>', methods=['GET'])
    def view_conversation(conversation_id):
        """View a specific conversation"""
        user_id = session.get('user_id')
        
        if not user_id:
            flash('Please log in to view conversations', 'error')
            return redirect(url_for('index'))
        
        conversation = Conversation.query.get(conversation_id)
        
        if not conversation or conversation.user_id != user_id:
            flash('Conversation not found or access denied', 'error')
            return redirect(url_for('view_conversations'))
        
        messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.timestamp).all()
        
        return render_template('index.html', 
                             active_conversation=conversation,
                             messages=messages)
    
    # ======= THOR Advanced Capabilities Routes =======
    
    @app.route('/api/thor/generate-code', methods=['POST'])
    def thor_generate_code():
        """API endpoint for code generation"""
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User not logged in'}), 401
        
        data = request.json
        description = data.get('description', '')
        language = data.get('language', 'python')
        
        if not description:
            return jsonify({'error': 'Code description is required'}), 400
        
        try:
            result = ai_engine.generate_code(description, language)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error generating code: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Error generating code: {str(e)}'
            }), 500
    
    @app.route('/api/thor/analyze-code', methods=['POST'])
    def thor_analyze_code():
        """API endpoint for code analysis"""
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User not logged in'}), 401
        
        data = request.json
        code = data.get('code', '')
        
        if not code:
            return jsonify({'error': 'Code is required'}), 400
        
        try:
            result = ai_engine.analyze_code(code)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error analyzing code: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Error analyzing code: {str(e)}'
            }), 500
    
    @app.route('/api/thor/create-dataset', methods=['POST'])
    def thor_create_dataset():
        """API endpoint for dataset creation"""
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User not logged in'}), 401
        
        data = request.json
        description = data.get('description', '')
        format_type = data.get('format', 'json')
        size = data.get('size', 10)
        
        if not description:
            return jsonify({'error': 'Dataset description is required'}), 400
        
        try:
            result = ai_engine.create_dataset(description, format_type, size)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error creating dataset: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Error creating dataset: {str(e)}'
            }), 500
    
    @app.route('/api/thor/network-scan', methods=['POST'])
    def thor_network_scan():
        """API endpoint for network scanning code generation"""
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User not logged in'}), 401
        
        data = request.json
        target_description = data.get('target_description', '')
        
        if not target_description:
            return jsonify({'error': 'Target description is required'}), 400
        
        try:
            result = ai_engine.network_scan(target_description)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error generating network scan: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Error generating network scan: {str(e)}'
            }), 500
    
    @app.route('/api/thor/suggest-improvements', methods=['POST'])
    def thor_suggest_improvements():
        """API endpoint for THOR self-improvement suggestions"""
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User not logged in'}), 401
        
        try:
            result = ai_engine.suggest_improvements()
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error suggesting improvements: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Error suggesting improvements: {str(e)}'
            }), 500
    
    # ======= THOR Clone Management Routes =======
    
    @app.route('/api/thor/create-clone', methods=['POST'])
    def thor_create_clone():
        """API endpoint for THOR clone creation"""
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User not logged in'}), 401
        
        data = request.json
        description = data.get('description', '')
        
        if not description:
            return jsonify({'error': 'Clone description is required'}), 400
        
        try:
            result = ai_engine.create_clone(description)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error creating clone: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Error creating clone: {str(e)}'
            }), 500
    
    @app.route('/api/thor/list-clones', methods=['GET'])
    def thor_list_clones():
        """API endpoint to list all THOR clones"""
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User not logged in'}), 401
        
        try:
            result = ai_engine.list_clones()
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error listing clones: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Error listing clones: {str(e)}'
            }), 500
    
    @app.route('/api/thor/activate-clone', methods=['POST'])
    def thor_activate_clone():
        """API endpoint to activate a THOR clone"""
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User not logged in'}), 401
        
        data = request.json
        clone_name = data.get('clone_name', '')
        
        if not clone_name:
            return jsonify({'error': 'Clone name is required'}), 400
        
        try:
            result = ai_engine.activate_clone(clone_name)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error activating clone: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Error activating clone: {str(e)}'
            }), 500
    
    @app.route('/api/thor/deactivate-clones', methods=['POST'])
    def thor_deactivate_clones():
        """API endpoint to deactivate all THOR clones"""
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User not logged in'}), 401
        
        try:
            result = ai_engine.deactivate_clones()
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error deactivating clones: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Error deactivating clones: {str(e)}'
            }), 500
    
    @app.route('/api/thor/update-clone', methods=['POST'])
    def thor_update_clone():
        """API endpoint to update a THOR clone"""
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User not logged in'}), 401
        
        data = request.json
        clone_name = data.get('clone_name', '')
        updates = data.get('updates', {})
        
        if not clone_name:
            return jsonify({'error': 'Clone name is required'}), 400
        if not updates:
            return jsonify({'error': 'Updates are required'}), 400
        
        try:
            result = ai_engine.update_clone(clone_name, updates)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error updating clone: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Error updating clone: {str(e)}'
            }), 500
                             
    # Return success to indicate routes were registered
    return True
