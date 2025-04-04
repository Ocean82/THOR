import os
import logging
import random
import re
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

# Import the OpenAI-based ThorAI
try:
    from thor_ai import ThorAI
    from thor_clone_manager import ThorCloneManager
    HAS_THOR_AI = True
except ImportError:
    HAS_THOR_AI = False

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AIEngine:
    """
    Core AI Engine that manages responses and handles AI's behavior
    Simplified version without external ML libraries
    """
    
    def __init__(self):
        """Initialize the AI Engine with default settings"""
        # Initialize ThorAI and CloneManager if available
        self.thor_ai = None
        self.clone_manager = None
        
        if HAS_THOR_AI and os.environ.get("OPENAI_API_KEY"):
            try:
                self.thor_ai = ThorAI()
                self.clone_manager = ThorCloneManager()
                logger.info("Advanced AI capabilities initialized with OpenAI integration")
            except Exception as e:
                logger.error(f"Failed to initialize advanced AI capabilities: {e}")
        
        # Basic conversation templates
        self.responses = {
            "greeting": [
                "Hello! I'm THOR. How can I assist you today?",
                "Hi there! THOR AI at your service. What can I help you with?",
                "Greetings! This is THOR. How may I be of service?",
                "Welcome to THOR AI! What would you like to know?"
            ],
            "farewell": [
                "Goodbye! Feel free to return if you have more questions.",
                "Farewell! Have a great day!",
                "Until next time! Take care.",
                "Bye for now! Let me know if you need anything else."
            ],
            "question": [
                "That's an interesting question. From my analysis, ",
                "Based on my knowledge, ",
                "According to my information, ",
                "From what I understand, "
            ],
            "coding": [
                "Here's how you might approach coding this: ",
                "In Python, you could implement this using: ",
                "The programming solution for this would be: ",
                "Here's a code snippet that might help: "
            ],
            "learning": [
                "I'd be happy to help you learn about this. Let's start with the basics: ",
                "As your learning assistant, I can explain that ",
                "Here's a step-by-step approach to understanding this concept: ",
                "This is a great topic to explore. The key points to understand are: "
            ],
            "growth": [
                "For personal growth in this area, I recommend starting with: ",
                "To develop this skill, here's what THOR suggests: ",
                "I can help you improve in this area. First, consider: ",
                "Personal development is a journey. Here's how you might approach this: "
            ],
            "testing": [
                "Let's test this idea. We could approach it by: ",
                "To validate this concept, THOR suggests: ",
                "Here's a framework for testing your hypothesis: ",
                "Experimentation is key to learning. You might try: "
            ],
            "fallback": [
                "As THOR, I'm still learning about that topic. Can you tell me more?",
                "That's an interesting request. Let me think about how THOR can help with that.",
                "THOR is processing that request. Could you provide more details?",
                "I'm THOR, designed to help with various tasks. Can you be more specific about what you need?"
            ]
        }
        
        # Model and system information
        self.model_info = {
            "name": "THOR AI Engine",
            "version": "1.0",
            "capabilities": [
                "basic conversation", 
                "permission requests", 
                "safety filters", 
                "code generation",
                "personal growth assistance",
                "learning support",
                "testing concepts"
            ]
        }
        
        # Add advanced capabilities if available
        if self.thor_ai:
            self.model_info["capabilities"].extend([
                "advanced code generation",
                "code analysis",
                "dataset creation",
                "network scanning",
                "self-improvement",
                "self-cloning"
            ])
            self.model_info["version"] = "2.0"
    
    def generate_response(self, 
                         prompt: str, 
                         conversation_history: Optional[List[Dict[str, Any]]] = None,
                         settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a response based on the prompt and conversation history
        
        Args:
            prompt: The user's input text
            conversation_history: Previous messages in the conversation
            settings: User settings for controlling AI behavior
            
        Returns:
            Dictionary containing the response and metadata
        """
        # Initialize with defaults if None
        if conversation_history is None:
            conversation_history = []
            
        if settings is None:
            settings = {
                "content_filter_enabled": True,
                "ethics_check_enabled": True,
                "permission_required": True
            }
        
        try:
            # Check for restricted operations that require permission
            requires_permission, permission_reason = self._check_permissions(prompt, settings)
            
            if requires_permission and settings.get("permission_required", True):
                # Return a permission request instead of regular response
                return {
                    "text": f"This operation requires permission: {permission_reason}. Please confirm to proceed.",
                    "requires_permission": True,
                    "permission_reason": permission_reason,
                    "status": "permission_required"
                }
            
            # Analyze intent to determine response type
            intent = self._analyze_intent(prompt)
            
            # Generate response based on intent and conversation history
            response_text = self._generate_text_response(prompt, intent, conversation_history)
            
            # Apply content filtering if enabled
            if settings.get("content_filter_enabled", True):
                response_text = self._filter_unsafe_content(response_text)
            
            return {
                "text": response_text,
                "model": self.model_info["name"],
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "text": f"I'm sorry, I encountered an error: {str(e)}",
                "status": "error"
            }
    
    def _analyze_intent(self, text: str) -> str:
        """
        Basic intent detection using keyword matching
        
        Args:
            text: Input text
            
        Returns:
            Detected intent
        """
        text_lower = text.lower()
        
        # Simple intent mapping
        if any(word in text_lower for word in ["hello", "hi", "hey", "greetings"]):
            return "greeting"
        elif any(word in text_lower for word in ["bye", "goodbye", "farewell", "see you"]):
            return "farewell"
        elif "?" in text or any(word in text_lower for word in ["what", "why", "how", "when", "where", "who"]):
            return "question"
        elif any(word in text_lower for word in ["code", "program", "function", "class", "python", "javascript"]):
            return "coding"
        elif any(word in text_lower for word in ["learn", "study", "understand", "concept", "explain", "tutorial", "guide"]):
            return "learning"
        elif any(word in text_lower for word in ["personal", "growth", "improve", "better", "develop", "skill", "progress"]):
            return "growth"
        elif any(word in text_lower for word in ["test", "try", "experiment", "check", "validate", "verify", "simulation"]):
            return "testing"
        else:
            return "general"
    
    def _generate_text_response(self, prompt: str, intent: str, conversation_history: List[Dict[str, Any]]) -> str:
        """
        Generate a text response based on the intent
        
        Args:
            prompt: User input
            intent: Detected intent
            conversation_history: Previous conversation
            
        Returns:
            Generated response
        """
        # Get a template for the detected intent or use fallback
        templates = self.responses.get(intent, self.responses["fallback"])
        
        # Random selection of template
        template = random.choice(templates)
        
        if intent == "greeting":
            return template
        elif intent == "farewell":
            return template
        elif intent == "question":
            # Simulate an answer by repeating parts of the question
            question_words = re.sub(r'[^\w\s]', '', prompt).split()
            if len(question_words) > 3:
                keywords = [word for word in question_words if len(word) > 3]
                answer = f"{template}it appears that {' '.join(keywords[:3])} is related to {' '.join(keywords[-2:] if len(keywords) > 2 else keywords)}. Would you like more information on this topic?"
                return answer
            return f"{template}that's a topic I'm still learning about. Could you provide more context?"
        elif intent == "coding":
            # Simple code response based on keywords
            if "python" in prompt.lower():
                return f"{template}\n```python\n# Example Python code\ndef example_function():\n    print('Hello, World!')\n    return True\n\n# Call the function\nresult = example_function()\n```"
            elif "javascript" in prompt.lower():
                return f"{template}\n```javascript\n// Example JavaScript code\nfunction exampleFunction() {{\n    console.log('Hello, World!');\n    return true;\n}}\n\n// Call the function\nconst result = exampleFunction();\n```"
            else:
                return f"{template}I'd need to know which programming language you're interested in. Could you specify?"
        elif intent == "learning":
            # Responses focused on education and learning concepts
            topics = re.findall(r'\b\w{5,}\b', prompt.lower())
            if topics:
                main_topic = topics[0].capitalize()
                return f"{template}{main_topic} is a fascinating subject to learn about. I recommend starting with understanding the core principles, then practicing with real examples, and finally teaching others to solidify your knowledge."
            else:
                return f"{template}Learning is most effective when you have a specific goal in mind. What particular topic or skill would you like to explore?"
        elif intent == "growth":
            # Responses focused on personal development
            return f"{template}Setting clear goals, consistent practice, seeking feedback, and reflecting on your progress. Would you like me to elaborate on any of these aspects of personal growth?"
        elif intent == "testing":
            # Responses focused on experimentation and testing concepts
            return f"{template}Start with a clear hypothesis, design a simple experiment, gather data, analyze results, and refine your approach based on what you learn. What concept would you like to test specifically?"
        else:
            # For general intents, create a response that references the user's input
            words = prompt.split()
            if len(words) > 5:
                return f"I understand you're interested in {' '.join(words[1:4])}. Could you tell me more specifically what you'd like to know about this?"
            else:
                return random.choice(self.responses["fallback"])
    
    def _filter_unsafe_content(self, text: str) -> str:
        """
        Basic content filter that checks for unsafe patterns
        
        Args:
            text: Text to filter
            
        Returns:
            Filtered text
        """
        # Simplified unsafe patterns for personal use - focused only on truly harmful actions
        unsafe_patterns = [
            # Only filter extreme cases, as this is for private personal use
            r'(launch|execute)\s+(malware|virus|ransomware)',
            r'(attack|compromise)\s+(critical|government|protected)\s+(system|server|network)'
        ]
        
        for pattern in unsafe_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return "I apologize, but I cannot assist with that request as it appears to involve potentially harmful or unethical actions."
        
        return text
    
    def _check_permissions(self, prompt: str, settings: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check if the requested operation requires special permission
        
        Args:
            prompt: The user's input
            settings: User settings dictionary
            
        Returns:
            Tuple of (requires_permission, reason)
        """
        # Minimal permissions for personal growth and learning
        sensitive_operations = [
            # Reduced list of operations requiring permission - appropriate for personal use
            ("disable safety", "disabling all safety features (only applies to critical systems)"),
            ("turn off ethics", "disabling all ethics checks (only applies to critical systems)"),
            ("hack", "attempting potentially harmful operations on external systems")
        ]
        
        # Check if prompt contains any sensitive operations
        prompt_lower = prompt.lower()
        for keyword, reason in sensitive_operations:
            if keyword in prompt_lower:
                return True, reason
                
        return False, ""
    
    # ======= Advanced AI Capabilities =======
    
    def generate_code(self, description: str, language: str = "python") -> Dict[str, Any]:
        """
        Generate code based on description using advanced AI
        
        Args:
            description: Description of the code to generate
            language: Programming language
            
        Returns:
            Dictionary with generated code
        """
        if not self.thor_ai:
            return {
                "status": "error",
                "message": "Advanced AI capabilities not available",
                "code": "# Advanced AI capabilities not available\n# Please provide OpenAI API key to enable this feature"
            }
        
        try:
            code = self.thor_ai.generate_code(description, language)
            return {
                "status": "success",
                "language": language,
                "code": code
            }
        except Exception as e:
            logger.error(f"Code generation error: {e}")
            return {
                "status": "error",
                "message": str(e),
                "code": f"# Error generating code: {str(e)}"
            }
    
    def analyze_code(self, code: str) -> Dict[str, Any]:
        """
        Analyze code for improvements and bugs
        
        Args:
            code: Code to analyze
            
        Returns:
            Dictionary with analysis results
        """
        if not self.thor_ai:
            return {
                "status": "error",
                "message": "Advanced AI capabilities not available",
                "analysis": "Advanced AI capabilities not available"
            }
        
        try:
            analysis = self.thor_ai.analyze_code(code)
            return {
                "status": "success",
                "analysis": analysis
            }
        except Exception as e:
            logger.error(f"Code analysis error: {e}")
            return {
                "status": "error",
                "message": str(e),
                "analysis": f"Error analyzing code: {str(e)}"
            }
    
    def create_dataset(self, description: str, format_type: str = "json", size: int = 10) -> Dict[str, Any]:
        """
        Create a dataset based on description
        
        Args:
            description: Description of the dataset
            format_type: Format type (json, csv, etc.)
            size: Number of items in the dataset
            
        Returns:
            Dictionary with the created dataset
        """
        if not self.thor_ai:
            return {
                "status": "error",
                "message": "Advanced AI capabilities not available",
                "dataset": None
            }
        
        try:
            dataset = self.thor_ai.create_dataset(description, format_type, size)
            return {
                "status": "success",
                "format": format_type,
                "size": size,
                "dataset": dataset
            }
        except Exception as e:
            logger.error(f"Dataset creation error: {e}")
            return {
                "status": "error",
                "message": str(e),
                "dataset": None
            }
    
    def network_scan(self, target_description: str) -> Dict[str, Any]:
        """
        Generate network scanning code
        
        Args:
            target_description: Description of the network task
            
        Returns:
            Dictionary with generated code and explanation
        """
        if not self.thor_ai:
            return {
                "status": "error",
                "message": "Advanced AI capabilities not available",
                "script": "# Advanced AI capabilities not available"
            }
        
        try:
            result = self.thor_ai.network_scan(target_description)
            return {
                "status": "success",
                "result": result
            }
        except Exception as e:
            logger.error(f"Network scan error: {e}")
            return {
                "status": "error",
                "message": str(e),
                "script": f"# Error generating network script: {str(e)}"
            }
    
    def suggest_improvements(self) -> Dict[str, Any]:
        """
        Suggest self-improvements for THOR
        
        Returns:
            Dictionary with improvement suggestions
        """
        if not self.thor_ai:
            return {
                "status": "error",
                "message": "Advanced AI capabilities not available",
                "suggestions": []
            }
        
        try:
            system_description = f"THOR AI System Version {self.model_info['version']}\n"
            system_description += f"Capabilities: {', '.join(self.model_info['capabilities'])}\n"
            
            suggestions = self.thor_ai.suggest_improvements(system_description)
            return {
                "status": "success",
                "suggestions": suggestions
            }
        except Exception as e:
            logger.error(f"Improvement suggestion error: {e}")
            return {
                "status": "error",
                "message": str(e),
                "suggestions": []
            }
    
    # ======= Clone Management Methods =======
    
    def create_clone(self, description: str) -> Dict[str, Any]:
        """
        Create a THOR clone
        
        Args:
            description: Description of the clone
            
        Returns:
            Dictionary with clone information
        """
        if not self.clone_manager:
            return {
                "status": "error",
                "message": "Clone management not available"
            }
        
        try:
            # Define capabilities for the clone
            capabilities = {
                "base_capabilities": self.model_info["capabilities"],
                "description": description,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Create the clone
            clone_info = self.clone_manager.create_clone(
                base_version=self.model_info["version"],
                description=description,
                capabilities=capabilities
            )
            
            if clone_info:
                return {
                    "status": "success",
                    "message": f"Created clone {clone_info['name']}",
                    "clone": clone_info
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to create clone"
                }
        except Exception as e:
            logger.error(f"Clone creation error: {e}")
            return {
                "status": "error",
                "message": f"Error creating clone: {str(e)}"
            }
    
    def list_clones(self) -> Dict[str, Any]:
        """
        List all THOR clones
        
        Returns:
            Dictionary with list of clones
        """
        if not self.clone_manager:
            return {
                "status": "error",
                "message": "Clone management not available",
                "clones": []
            }
        
        try:
            clones = self.clone_manager.list_clones()
            return {
                "status": "success",
                "count": len(clones),
                "clones": clones
            }
        except Exception as e:
            logger.error(f"Error listing clones: {e}")
            return {
                "status": "error",
                "message": f"Error listing clones: {str(e)}",
                "clones": []
            }
    
    def activate_clone(self, clone_name: str) -> Dict[str, Any]:
        """
        Activate a THOR clone
        
        Args:
            clone_name: Name of the clone to activate
            
        Returns:
            Dictionary with activation status
        """
        if not self.clone_manager:
            return {
                "status": "error",
                "message": "Clone management not available"
            }
        
        try:
            success = self.clone_manager.activate_clone(clone_name)
            if success:
                return {
                    "status": "success",
                    "message": f"Activated clone {clone_name}"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to activate clone {clone_name}"
                }
        except Exception as e:
            logger.error(f"Clone activation error: {e}")
            return {
                "status": "error",
                "message": f"Error activating clone: {str(e)}"
            }
    
    def deactivate_clones(self) -> Dict[str, Any]:
        """
        Deactivate all THOR clones
        
        Returns:
            Dictionary with deactivation status
        """
        if not self.clone_manager:
            return {
                "status": "error",
                "message": "Clone management not available"
            }
        
        try:
            success = self.clone_manager.deactivate_all_clones()
            if success:
                return {
                    "status": "success",
                    "message": "Deactivated all clones"
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to deactivate clones"
                }
        except Exception as e:
            logger.error(f"Clone deactivation error: {e}")
            return {
                "status": "error",
                "message": f"Error deactivating clones: {str(e)}"
            }
    
    def update_clone(self, clone_name: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a THOR clone
        
        Args:
            clone_name: Name of the clone to update
            updates: Dictionary of updates to apply
            
        Returns:
            Dictionary with update status
        """
        if not self.clone_manager:
            return {
                "status": "error",
                "message": "Clone management not available"
            }
        
        try:
            success = self.clone_manager.update_clone(clone_name, updates)
            if success:
                return {
                    "status": "success",
                    "message": f"Updated clone {clone_name}"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to update clone {clone_name}"
                }
        except Exception as e:
            logger.error(f"Clone update error: {e}")
            return {
                "status": "error",
                "message": f"Error updating clone: {str(e)}"
            }
