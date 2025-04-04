import os
import logging
from typing import Dict, List, Tuple, Optional, Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import nltk

from model_integrator import ModelIntegrator
from nlp_processor import NLPProcessor

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AIEngine:
    """
    Core AI Engine that manages models, processes requests, and handles the AI's responses
    """
    
    def __init__(self):
        """Initialize the AI Engine with default settings and components"""
        self.model_integrator = ModelIntegrator()
        self.nlp_processor = NLPProcessor()
        
        # Default model settings
        self.current_model_name = "gpt2"  # Starting with a small model
        self.current_model = None
        self.current_tokenizer = None
        
        # Attempt to load NLTK requirements
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)
        except Exception as e:
            logger.warning(f"Failed to download NLTK resources: {e}")
        
        # Load default model
        self.load_model(self.current_model_name)
    
    def load_model(self, model_name: str) -> bool:
        """
        Load a model by name, either from cache or by downloading
        
        Args:
            model_name: The name of the model to load
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if model exists in cache or needs downloading
            model_path = self.model_integrator.get_model_path(model_name)
            
            # Load the model and tokenizer
            self.current_model = AutoModelForCausalLM.from_pretrained(model_path)
            self.current_tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.current_model_name = model_name
            
            logger.info(f"Successfully loaded model: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            return False
    
    def generate_response(self, 
                         prompt: str, 
                         conversation_history: List[Dict[str, Any]] = None,
                         settings: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate a response based on the prompt and conversation history
        
        Args:
            prompt: The user's input text
            conversation_history: Previous messages in the conversation
            settings: User settings for controlling AI behavior
            
        Returns:
            Dictionary containing the response and metadata
        """
        if conversation_history is None:
            conversation_history = []
            
        if settings is None:
            settings = {
                "content_filter_enabled": True,
                "ethics_check_enabled": True,
                "permission_required": True,
                "max_length": 100
            }
        
        try:
            # Prepare input by combining conversation history and prompt
            full_prompt = self._prepare_prompt(prompt, conversation_history)
            
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
            
            # Process with model
            inputs = self.current_tokenizer(full_prompt, return_tensors="pt")
            max_length = settings.get("max_length", 100) + len(inputs["input_ids"][0])
            
            with torch.no_grad():
                outputs = self.current_model.generate(
                    inputs["input_ids"],
                    max_length=max_length,
                    num_return_sequences=1,
                    temperature=settings.get("temperature", 0.7),
                    top_p=settings.get("top_p", 0.9),
                    do_sample=True
                )
            
            # Decode the output
            generated_text = self.current_tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract just the new response (not the prompt)
            response_text = generated_text[len(full_prompt):].strip()
            
            # Process response with NLP processor
            processed_response = self.nlp_processor.process_text(response_text)
            
            # Apply content filtering if enabled
            if settings.get("content_filter_enabled", True):
                processed_response = self.nlp_processor.filter_unsafe_content(processed_response)
            
            return {
                "text": processed_response,
                "model": self.current_model_name,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "text": f"I'm sorry, I encountered an error: {str(e)}",
                "status": "error"
            }
    
    def _prepare_prompt(self, prompt: str, conversation_history: List[Dict[str, Any]]) -> str:
        """
        Format conversation history and current prompt into a format the model can use
        
        Args:
            prompt: Current user input
            conversation_history: List of previous messages
            
        Returns:
            Formatted prompt string
        """
        formatted_conversation = ""
        
        # Add conversation history
        for message in conversation_history[-5:]:  # Only use last 5 messages to avoid context length issues
            speaker = "User: " if message.get("is_user", False) else "AI: "
            formatted_conversation += f"{speaker}{message.get('content', '')}\n"
        
        # Add current prompt
        formatted_conversation += f"User: {prompt}\nAI:"
        
        return formatted_conversation
    
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
