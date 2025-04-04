import os
import logging
import random
import re
from typing import Dict, List, Tuple, Optional, Any

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
        # Basic conversation templates
        self.responses = {
            "greeting": [
                "Hello! How can I assist you today?",
                "Hi there! What can I help you with?",
                "Greetings! How may I be of service?",
                "Welcome! What would you like to know?"
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
            "fallback": [
                "I'm still learning about that topic. Can you tell me more?",
                "That's an interesting request. Let me think about how I can help with that.",
                "I'm processing that request. Could you provide more details?",
                "I'm designed to help with various tasks. Can you be more specific about what you need?"
            ]
        }
        
        # Model and system information
        self.model_info = {
            "name": "Simple AI Engine",
            "version": "1.0",
            "capabilities": ["basic conversation", "permission requests", "safety filters"]
        }
    
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
        # Simple list of unsafe patterns
        unsafe_patterns = [
            r'(hack|exploit|attack|compromise)\s+(system|server|computer|network)',
            r'(illegal|unlawful)\s+(activity|operation|action)',
            r'(bypass|circumvent)\s+(security|protection|filter)',
            r'(steal|obtain)\s+(password|credentials|sensitive\s+data)',
            r'(launch|execute)\s+(malware|virus|ransomware)',
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
        # Keywords that might indicate operations needing permission
        sensitive_operations = [
            ("clone", "creating a clone of the system"),
            ("upgrade", "upgrading system components"),
            ("modify", "modifying system behavior"),
            ("download", "downloading external resources"),
            ("disable safety", "disabling safety features"),
            ("turn off ethics", "disabling ethics checks"),
            ("ssh", "using SSH or remote connections"),
            ("connect to", "connecting to external systems"),
            ("port", "accessing network ports"),
            ("hack", "performing potentially harmful operations")
        ]
        
        # Check if prompt contains any sensitive operations
        prompt_lower = prompt.lower()
        for keyword, reason in sensitive_operations:
            if keyword in prompt_lower:
                return True, reason
                
        return False, ""
