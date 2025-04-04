"""
Anthropic API Integration module for THOR AI system
"""
import json
import os
import sys
import logging
from typing import Dict, Any, List, Optional, Tuple

import anthropic
from anthropic import Anthropic

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# The newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
DEFAULT_MODEL = "claude-3-5-sonnet-20241022"

class AnthropicAI:
    """
    Handles interaction with Anthropic's Claude API as an alternative to OpenAI
    """
    
    def __init__(self):
        """Initialize the Anthropic client with API key"""
        self.api_key = os.environ.get('ANTHROPIC_API_KEY')
        
        if not self.api_key:
            logger.error("ANTHROPIC_API_KEY environment variable not set")
        
        try:
            self.client = Anthropic(api_key=self.api_key)
            logger.info("Anthropic client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Anthropic client: {e}")
            self.client = None
    
    def generate_text(self, prompt: str, 
                     conversation_history: Optional[List[Dict[str, Any]]] = None,
                     max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Generate text response using Claude
        
        Args:
            prompt: The prompt to send to Claude
            conversation_history: Previous conversation messages
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dictionary with response text and metadata
        """
        if not self.client:
            return {
                "text": "Unable to access Anthropic API. Please check your API key.",
                "error": "Client initialization failed"
            }
        
        # Build messages list for Claude format
        messages = self._build_messages(prompt, conversation_history)
        
        try:
            response = self.client.messages.create(
                model=DEFAULT_MODEL,
                messages=messages,
                max_tokens=max_tokens
            )
            
            return {
                "text": response.content[0].text,
                "model": response.model,
                "provider": "anthropic"
            }
        except Exception as e:
            error_msg = f"Error generating text with Anthropic: {e}"
            logger.error(error_msg)
            return {
                "text": "I apologize, but I encountered an error while processing your request.",
                "error": error_msg
            }
    
    def _build_messages(self, prompt: str, 
                       conversation_history: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Build messages in Anthropic format from conversation history
        
        Args:
            prompt: Current user prompt
            conversation_history: Previous conversation messages
            
        Returns:
            List of formatted messages for Claude API
        """
        messages = []
        
        # Add conversation history if available
        if conversation_history:
            for msg in conversation_history:
                role = "user" if msg.get("is_user", True) else "assistant"
                messages.append({"role": role, "content": msg.get("content", "")})
        
        # Add current prompt
        messages.append({"role": "user", "content": prompt})
        
        return messages
    
    def generate_code(self, description: str, language: str = "python") -> Dict[str, Any]:
        """
        Generate code based on description
        
        Args:
            description: Description of the code to generate
            language: Programming language
            
        Returns:
            Dictionary with generated code
        """
        prompt = f"""Generate {language} code based on this description:
        
{description}

Please provide only the code, without explanations. Use best practices and include comments where appropriate."""
        
        response = self.generate_text(prompt)
        
        # Extract code from the response
        code = response.get("text", "")
        
        return {
            "code": code,
            "language": language,
            "provider": "anthropic"
        }
    
    def analyze_code(self, code: str) -> Dict[str, Any]:
        """
        Analyze code for improvements and bugs
        
        Args:
            code: Code to analyze
            
        Returns:
            Dictionary with analysis results
        """
        prompt = f"""Analyze this code for potential improvements, bugs, and best practices:
        
```
{code}
```

Provide your analysis with the following sections:
1. Potential bugs and issues
2. Performance considerations
3. Best practices and improvements
4. Security concerns (if applicable)
"""
        
        response = self.generate_text(prompt)
        
        return {
            "analysis": response.get("text", ""),
            "provider": "anthropic"
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
        prompt = f"""Create a {format_type} dataset with {size} items based on this description:
        
{description}

Only provide the dataset in valid {format_type} format, without explanations."""
        
        response = self.generate_text(prompt)
        
        return {
            "dataset": response.get("text", ""),
            "format": format_type,
            "provider": "anthropic"
        }
    
    def network_scan(self, target_description: str) -> Dict[str, Any]:
        """
        Generate network scanning code
        
        Args:
            target_description: Description of the network task
            
        Returns:
            Dictionary with generated code and explanation
        """
        prompt = f"""Generate Python code for network scanning or analysis based on this description:
        
{target_description}

Provide code that uses standard Python libraries like socket, requests, or specialized libraries like scapy, nmap-python, etc.
Include comments explaining how the code works and any security or ethical considerations."""
        
        response = self.generate_text(prompt)
        
        return {
            "script": response.get("text", ""),
            "provider": "anthropic"
        }
    
    def suggest_improvements(self) -> Dict[str, Any]:
        """
        Suggest self-improvements for THOR
        
        Returns:
            Dictionary with improvement suggestions
        """
        prompt = """You are THOR, an advanced AI system. Suggest improvements for your own capabilities, features, and architecture.
        
Focus on:
1. Technical improvements to your core functionality
2. New features that would enhance your usefulness
3. User experience improvements
4. Security and safety enhancements
5. Ways to better integrate with external systems

Be specific in your suggestions and explain the benefits of each improvement."""
        
        response = self.generate_text(prompt)
        
        # Try to parse the response into structured suggestions
        try:
            # Return raw text response
            return {
                "suggestions": response.get("text", "").split("\n"),
                "provider": "anthropic"
            }
        except Exception as e:
            logger.error(f"Error parsing improvement suggestions: {e}")
            return {
                "suggestions": [response.get("text", "")],
                "provider": "anthropic",
                "error": f"Error parsing structure: {e}"
            }