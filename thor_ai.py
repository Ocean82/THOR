import json
import os
import logging
from typing import List, Dict, Any, Optional, Union

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
from openai import OpenAI

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = OpenAI(api_key=OPENAI_API_KEY)


class ThorAI:
    """
    Advanced AI capabilities for THOR using OpenAI integration
    """
    
    def __init__(self, model_version="gpt-4o"):
        """
        Initialize the THOR AI with the specified model version
        """
        self.model_version = model_version
        self.client = openai
        logger.info(f"THOR AI initialized with model: {model_version}")
    
    def generate_code(self, prompt: str, language: str = "python") -> str:
        """
        Generate code based on the provided prompt
        
        Args:
            prompt: Description of the code to generate
            language: Programming language (default: python)
            
        Returns:
            Generated code as a string
        """
        try:
            full_prompt = f"Generate {language} code for the following: {prompt}\n"
            full_prompt += f"Only output the code, no explanations.\n"
            
            system_message = f"""You are an expert programming AI assistant specializing in {language}.
Your role is to:
1. Understand programming concepts deeply and explain them clearly
2. Generate working, well-documented code with best practices
3. Learn from context and adapt responses accordingly
4. Provide relevant code examples and explanations
5. Focus on practical, maintainable solutions"""

            response = self.client.chat.completions.create(
                model=self.model_version,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=4000,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Code generation error: {e}")
            return f"Error generating code: {str(e)}"
    
    def analyze_code(self, code: str) -> Dict[str, Any]:
        """
        Analyze code for improvements, bugs, and enhancement opportunities
        
        Args:
            code: Code to analyze
            
        Returns:
            Dictionary with analysis results
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_version,
                messages=[
                    {"role": "system", "content": "You are an expert code reviewer. Analyze the code for bugs, improvements, and enhancement opportunities."},
                    {"role": "user", "content": f"Analyze this code and provide insights:\n\n{code}"}
                ],
                response_format={"type": "json_object"},
                max_tokens=2000
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Code analysis error: {e}")
            return {"error": str(e)}
    
    def create_dataset(self, description: str, format_type: str = "json", size: int = 10) -> Union[str, Dict[str, Any]]:
        """
        Create a sample dataset based on the provided description
        
        Args:
            description: Description of the dataset to create
            format_type: Format of the dataset (json, csv, etc.)
            size: Number of records to generate
            
        Returns:
            Generated dataset as a string or dictionary
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_version,
                messages=[
                    {"role": "system", "content": f"You are a data generation expert. Create a sample {format_type} dataset with {size} records."},
                    {"role": "user", "content": f"Create a {format_type} dataset with {size} records for: {description}"}
                ],
                max_tokens=4000
            )
            result = response.choices[0].message.content
            
            if format_type.lower() == "json":
                try:
                    return json.loads(result)
                except:
                    return result
            return result
        except Exception as e:
            logger.error(f"Dataset creation error: {e}")
            return {"error": str(e)}
    
    def network_scan(self, target_description: str) -> Dict[str, Any]:
        """
        Generate a simulated network scanning script based on description
        
        Args:
            target_description: Description of the network task
            
        Returns:
            Dictionary with script and explanation
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_version,
                messages=[
                    {"role": "system", "content": "You are a networking expert. Generate Python code using libraries like socket, requests, scapy, etc."},
                    {"role": "user", "content": f"Create a Python script for this networking task: {target_description}"}
                ],
                response_format={"type": "json_object"},
                max_tokens=4000
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Network task error: {e}")
            return {"error": str(e), "script": "# Error generating script"}
    
    def suggest_improvements(self, system_description: str) -> Dict[str, Any]:
        """
        Suggest improvements for self-evolution
        
        Args:
            system_description: Description of the current system
            
        Returns:
            Dictionary with improvement suggestions
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_version,
                messages=[
                    {"role": "system", "content": "You are THOR, an advanced AI system. Suggest improvements for self-evolution."},
                    {"role": "user", "content": f"Analyze this system and suggest improvements:\n\n{system_description}"}
                ],
                response_format={"type": "json_object"},
                max_tokens=2000
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Improvement suggestion error: {e}")
            return {"error": str(e), "suggestions": []}


# Test function to verify OpenAI connectivity
def test_openai_connection():
    """Test the OpenAI API connection"""
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'THOR AI connection successful'"}
            ],
            max_tokens=20
        )
        return {"success": True, "message": response.choices[0].message.content}
    except Exception as e:
        logger.error(f"OpenAI connection test failed: {e}")
        return {"success": False, "error": str(e)}