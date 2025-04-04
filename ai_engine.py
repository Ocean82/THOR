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
    
# Import the Anthropic-based AnthropicAI
try:
    from anthropic_ai import AnthropicAI
    HAS_ANTHROPIC_AI = True
except ImportError:
    HAS_ANTHROPIC_AI = False

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
        # Initialize ThorAI, AnthropicAI, and CloneManager if available
        self.thor_ai = None
        self.anthropic_ai = None
        self.clone_manager = None
        
        # Try to initialize OpenAI integration
        if HAS_THOR_AI and os.environ.get("OPENAI_API_KEY"):
            try:
                self.thor_ai = ThorAI()
                self.clone_manager = ThorCloneManager()
                logger.info("Advanced AI capabilities initialized with OpenAI integration")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI capabilities: {e}")
        
        # Try to initialize Anthropic integration (as a fallback or alternative)
        if HAS_ANTHROPIC_AI and os.environ.get("ANTHROPIC_API_KEY"):
            try:
                self.anthropic_ai = AnthropicAI()
                logger.info("Anthropic AI capabilities initialized successfully")
                # Initialize clone manager if not already done with OpenAI
                if not self.clone_manager and HAS_THOR_AI:
                    self.clone_manager = ThorCloneManager()
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic capabilities: {e}")
        
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
        if self.thor_ai or self.anthropic_ai:
            self.model_info["capabilities"].extend([
                "advanced code generation",
                "code analysis",
                "dataset creation",
                "network scanning",
                "self-improvement",
                "self-cloning"
            ])
            self.model_info["version"] = "2.0"
            
        # Add specific provider information
        if self.thor_ai and self.anthropic_ai:
            self.model_info["providers"] = ["OpenAI", "Anthropic"]
        elif self.thor_ai:
            self.model_info["providers"] = ["OpenAI"]
        elif self.anthropic_ai:
            self.model_info["providers"] = ["Anthropic"]
    
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
        # If no AI providers are available, use the built-in fallback
        if not self.thor_ai and not self.anthropic_ai:
            return self._generate_fallback_code(description, language)
        
        # Try OpenAI first if available
        if self.thor_ai:
            try:
                code = self.thor_ai.generate_code(description, language)
                return {
                    "status": "success",
                    "language": language,
                    "code": code,
                    "provider": "openai"
                }
            except Exception as e:
                logger.error(f"OpenAI code generation error: {e}")
                logger.info("Attempting to use Anthropic as fallback")
                
                # If Anthropic is available as fallback
                if self.anthropic_ai:
                    try:
                        result = self.anthropic_ai.generate_code(description, language)
                        return {
                            "status": "success",
                            "language": language,
                            "code": result.get("code", "# No code generated"),
                            "provider": "anthropic"
                        }
                    except Exception as e2:
                        logger.error(f"Anthropic fallback failed: {e2}")
                
                # If both fail or Anthropic isn't available, use built-in fallback
                logger.info("Falling back to basic code generation")
                return self._generate_fallback_code(description, language)
        
        # If only Anthropic is available
        elif self.anthropic_ai:
            try:
                result = self.anthropic_ai.generate_code(description, language)
                return {
                    "status": "success",
                    "language": language,
                    "code": result.get("code", "# No code generated"),
                    "provider": "anthropic"
                }
            except Exception as e:
                logger.error(f"Anthropic code generation error: {e}")
                logger.info("Falling back to basic code generation")
                return self._generate_fallback_code(description, language)
        
        # This shouldn't be reachable given the first if statement, but added to satisfy type checker
        return self._generate_fallback_code(description, language)
            
    def _generate_fallback_code(self, description: str, language: str) -> Dict[str, Any]:
        """
        Fallback code generation when OpenAI is not available
        
        Args:
            description: Description of the code to generate
            language: Programming language
            
        Returns:
            Dictionary with generated basic code
        """
        description_lower = description.lower()
        
        # Basic templates for different languages and common tasks
        templates = {
            "python": {
                "default": '# Simple Python program\n\ndef main():\n    print("Hello, World!")\n    # TODO: Implement functionality based on description\n    print("Description: {}")\n\nif __name__ == "__main__":\n    main()',
                "web": 'from flask import Flask, render_template, request\n\napp = Flask(__name__)\n\n@app.route("/")\ndef home():\n    return "Hello, World!"\n\nif __name__ == "__main__":\n    app.run(host="0.0.0.0", port=5000, debug=True)',
                "api": 'from flask import Flask, jsonify, request\n\napp = Flask(__name__)\n\n@app.route("/api/data", methods=["GET"])\ndef get_data():\n    return jsonify({"message": "Data endpoint"})\n\n@app.route("/api/data", methods=["POST"])\ndef post_data():\n    data = request.json\n    return jsonify({"received": data})\n\nif __name__ == "__main__":\n    app.run(host="0.0.0.0", port=5000, debug=True)',
                "data": 'import pandas as pd\nimport matplotlib.pyplot as plt\n\n# Load data (replace with your data source)\ndata = {"x": [1, 2, 3, 4, 5], "y": [10, 20, 25, 30, 35]}\ndf = pd.DataFrame(data)\n\n# Analyze data\nprint("Data Summary:")\nprint(df.describe())\n\n# Visualize data\nplt.figure(figsize=(10, 6))\nplt.plot(df["x"], df["y"], marker="o")\nplt.title("Data Visualization")\nplt.xlabel("X axis")\nplt.ylabel("Y axis")\nplt.grid(True)\nplt.show()',
                "ml": 'import numpy as np\nfrom sklearn.model_selection import train_test_split\nfrom sklearn.linear_model import LinearRegression\nfrom sklearn.metrics import mean_squared_error\n\n# Generate sample data\nX = np.random.rand(100, 1) * 10\ny = 2 * X + 1 + np.random.randn(100, 1)\n\n# Split data\nX_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)\n\n# Train model\nmodel = LinearRegression()\nmodel.fit(X_train, y_train)\n\n# Make predictions\ny_pred = model.predict(X_test)\n\n# Evaluate model\nmse = mean_squared_error(y_test, y_pred)\nprint(f"Mean Squared Error: {mse:.4f}")\nprint(f"Coefficient: {model.coef_[0][0]:.4f}")\nprint(f"Intercept: {model.intercept_[0]:.4f}")'
            },
            "javascript": {
                "default": '// Simple JavaScript program\n\nfunction main() {\n    console.log("Hello, World!");\n    // TODO: Implement functionality based on description\n    console.log("Description: {}");\n}\n\nmain();',
                "web": '// Simple web app\n\ndocument.addEventListener("DOMContentLoaded", function() {\n    const app = document.getElementById("app");\n    \n    if (app) {\n        app.innerHTML = `\n            <div class="container mt-5">\n                <h1>Hello, World!</h1>\n                <p>Welcome to my application</p>\n                <button id="actionBtn" class="btn btn-primary">Click Me</button>\n            </div>\n        `;\n        \n        document.getElementById("actionBtn").addEventListener("click", function() {\n            alert("Button clicked!");\n        });\n    }\n});',
                "api": '// API client example\n\nasync function fetchData() {\n    try {\n        const response = await fetch("https://api.example.com/data");\n        \n        if (!response.ok) {\n            throw new Error(`HTTP error! Status: ${response.status}`);\n        }\n        \n        const data = await response.json();\n        console.log("Data received:", data);\n        return data;\n    } catch (error) {\n        console.error("Error fetching data:", error);\n    }\n}\n\n// Example usage\nfetchData().then(data => {\n    // Process data here\n});',
                "react": 'import React, { useState, useEffect } from "react";\n\nfunction App() {\n    const [data, setData] = useState([]);\n    const [loading, setLoading] = useState(true);\n    \n    useEffect(() => {\n        // Fetch data when component mounts\n        fetch("https://api.example.com/data")\n            .then(response => response.json())\n            .then(data => {\n                setData(data);\n                setLoading(false);\n            })\n            .catch(error => {\n                console.error("Error fetching data:", error);\n                setLoading(false);\n            });\n    }, []);\n    \n    return (\n        <div className="App">\n            <h1>My React App</h1>\n            {loading ? (\n                <p>Loading data...</p>\n            ) : (\n                <ul>\n                    {data.map(item => (\n                        <li key={item.id}>{item.name}</li>\n                    ))}\n                </ul>\n            )}\n        </div>\n    );\n}\n\nexport default App;'
            },
            "java": {
                "default": 'public class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello, World!");\n        // TODO: Implement functionality based on description\n        System.out.println("Description: {}");\n    }\n}'
            },
            "cpp": {
                "default": '#include <iostream>\n\nint main() {\n    std::cout << "Hello, World!" << std::endl;\n    // TODO: Implement functionality based on description\n    std::cout << "Description: {}" << std::endl;\n    return 0;\n}'
            },
            "csharp": {
                "default": 'using System;\n\nclass Program {\n    static void Main(string[] args) {\n        Console.WriteLine("Hello, World!");\n        // TODO: Implement functionality based on description\n        Console.WriteLine("Description: {}");\n    }\n}'
            }
        }
        
        # Determine template category based on description
        category = "default"
        for keyword, cat in {
            "web": ["web", "website", "html", "css", "frontend", "app"],
            "api": ["api", "rest", "endpoint", "server", "request", "response"],
            "data": ["data", "processing", "csv", "pandas", "analysis", "plot", "graph"],
            "ml": ["machine learning", "ml", "ai", "model", "train", "predict"],
            "react": ["react", "component", "jsx", "frontend framework"]
        }.items():
            if any(word in description_lower for word in cat):
                category = keyword
                break
        
        # Get template for specified language or fallback to Python
        language_templates = templates.get(language.lower(), templates["python"])
        template = language_templates.get(category, language_templates["default"])
        
        # Format the template with the description
        code = template.format(description)
        
        return {
            "status": "success",
            "language": language,
            "code": code,
            "note": "Generated using THOR's basic templates (OpenAI integration unavailable)"
        }
    
    def analyze_code(self, code: str) -> Dict[str, Any]:
        """
        Analyze code for improvements and bugs
        
        Args:
            code: Code to analyze
            
        Returns:
            Dictionary with analysis results
        """
        # If no AI providers are available, use the built-in fallback
        if not self.thor_ai and not self.anthropic_ai:
            return self._generate_fallback_analysis(code)
        
        # Try OpenAI first if available
        if self.thor_ai:
            try:
                analysis = self.thor_ai.analyze_code(code)
                return {
                    "status": "success",
                    "analysis": analysis,
                    "provider": "openai"
                }
            except Exception as e:
                logger.error(f"OpenAI code analysis error: {e}")
                logger.info("Attempting to use Anthropic as fallback")
                
                # If Anthropic is available as fallback
                if self.anthropic_ai:
                    try:
                        result = self.anthropic_ai.analyze_code(code)
                        return {
                            "status": "success",
                            "analysis": result.get("analysis", "No analysis provided"),
                            "provider": "anthropic"
                        }
                    except Exception as e2:
                        logger.error(f"Anthropic fallback failed: {e2}")
                
                # If both fail or Anthropic isn't available, use built-in fallback
                logger.info("Falling back to basic code analysis")
                return self._generate_fallback_analysis(code)
        
        # If only Anthropic is available
        elif self.anthropic_ai:
            try:
                result = self.anthropic_ai.analyze_code(code)
                return {
                    "status": "success",
                    "analysis": result.get("analysis", "No analysis provided"),
                    "provider": "anthropic"
                }
            except Exception as e:
                logger.error(f"Anthropic code analysis error: {e}")
                logger.info("Falling back to basic code analysis")
                return self._generate_fallback_analysis(code)
                
        # This shouldn't be reachable given the first if statement, but added to satisfy type checker
        return self._generate_fallback_analysis(code)
            
    def _generate_fallback_analysis(self, code: str) -> Dict[str, Any]:
        """
        Fallback code analysis when OpenAI is not available
        
        Args:
            code: Code to analyze
            
        Returns:
            Dictionary with basic analysis
        """
        # Perform basic analysis
        analysis = {
            "summary": "Basic code analysis by THOR's built-in analyzer",
            "issues": [],
            "improvements": []
        }
        
        # Check for basic patterns and issues
        lines = code.split('\n')
        code_lower = code.lower()
        
        # Check for potential issues
        if "todo" in code_lower:
            analysis["issues"].append({
                "severity": "low",
                "title": "TODOs Found",
                "description": "The code contains TODO comments which indicate incomplete functionality."
            })
            
        if "print(" in code_lower and ("def " in code_lower or "class " in code_lower):
            analysis["issues"].append({
                "severity": "medium",
                "title": "Debug Print Statements",
                "description": "The code contains print statements which may not be suitable for production code. Consider using a logging framework instead."
            })
            
        if "except:" in code_lower and "pass" in code_lower:
            analysis["issues"].append({
                "severity": "high",
                "title": "Empty Except Block",
                "description": "The code contains empty except blocks which suppress exceptions without handling them properly."
            })
            
        if "import *" in code_lower:
            analysis["issues"].append({
                "severity": "medium",
                "title": "Wildcard Import",
                "description": "The code uses wildcard imports which can lead to namespace pollution. Consider importing only the specific modules or functions needed."
            })
            
        # Check language-specific patterns
        if "python" in code_lower or "def " in code_lower:
            # Python-specific analysis
            if "global " in code_lower:
                analysis["issues"].append({
                    "severity": "medium",
                    "title": "Global Variables",
                    "description": "The code uses global variables which can lead to maintainability issues. Consider using function parameters or class attributes."
                })
                
            # Check for potential improvements
            if "def " in code_lower and "docstring" not in code_lower and '"""' not in code and "'''" not in code:
                analysis["improvements"].append({
                    "title": "Add Docstrings",
                    "description": "Functions should have docstrings to explain their purpose, parameters, and return values.",
                    "example": '"""\nThis function does X with Y.\n\nArgs:\n    param1: Description of param1\n    \nReturns:\n    Description of return value\n"""'
                })
                
        elif "javascript" in code_lower or "function " in code_lower or "const " in code_lower:
            # JavaScript-specific analysis
            if "var " in code_lower:
                analysis["improvements"].append({
                    "title": "Use let/const Instead of var",
                    "description": "Modern JavaScript prefers let and const over var for variable declarations.",
                    "example": "const x = 5; // For constants\nlet y = 10; // For variables that change"
                })
                
        # Check complexity
        long_lines = [i+1 for i, line in enumerate(lines) if len(line.strip()) > 100]
        if long_lines:
            analysis["issues"].append({
                "severity": "low",
                "title": "Long Lines",
                "description": f"Lines {', '.join(map(str, long_lines[:3]))} {'and others ' if len(long_lines) > 3 else ''}are over 100 characters, which may reduce readability."
            })
            
        # Add count-based stats
        analysis["summary"] += f"\n\nBasic stats: {len(lines)} lines of code, {len(code.split())} words."
        
        # Generate generic improvements if none found
        if not analysis["improvements"]:
            analysis["improvements"].append({
                "title": "Add Comments",
                "description": "Consider adding more comments to explain complex logic and improve code readability."
            })
            
            analysis["improvements"].append({
                "title": "Write Unit Tests",
                "description": "Adding unit tests can help verify that your code works as expected and prevent regressions."
            })
            
        # Add note about limitations
        analysis["note"] = "Generated using THOR's basic code analyzer (OpenAI integration unavailable). This analysis is limited to pattern matching and may miss deeper issues."
        
        return {
            "status": "success",
            "analysis": analysis
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
        # If no AI providers are available, use the built-in fallback
        if not self.thor_ai and not self.anthropic_ai:
            return self._generate_fallback_dataset(description, format_type, size)
        
        # Try OpenAI first if available
        if self.thor_ai:
            try:
                dataset = self.thor_ai.create_dataset(description, format_type, size)
                return {
                    "status": "success",
                    "format": format_type,
                    "size": size,
                    "dataset": dataset,
                    "provider": "openai"
                }
            except Exception as e:
                logger.error(f"OpenAI dataset creation error: {e}")
                logger.info("Attempting to use Anthropic as fallback")
                
                # If Anthropic is available as fallback
                if self.anthropic_ai:
                    try:
                        result = self.anthropic_ai.create_dataset(description, format_type, size)
                        return {
                            "status": "success",
                            "format": format_type,
                            "size": size,
                            "dataset": result.get("dataset", "No dataset generated"),
                            "provider": "anthropic"
                        }
                    except Exception as e2:
                        logger.error(f"Anthropic fallback failed: {e2}")
                
                # If both fail or Anthropic isn't available, use built-in fallback
                logger.info("Falling back to basic dataset creation")
                return self._generate_fallback_dataset(description, format_type, size)
        
        # If only Anthropic is available
        elif self.anthropic_ai:
            try:
                result = self.anthropic_ai.create_dataset(description, format_type, size)
                return {
                    "status": "success",
                    "format": format_type,
                    "size": size,
                    "dataset": result.get("dataset", "No dataset generated"),
                    "provider": "anthropic"
                }
            except Exception as e:
                logger.error(f"Anthropic dataset creation error: {e}")
                logger.info("Falling back to basic dataset creation")
                return self._generate_fallback_dataset(description, format_type, size)
                
        # This shouldn't be reachable given the first if statement, but added to satisfy type checker
        return self._generate_fallback_dataset(description, format_type, size)
            
    def _generate_fallback_dataset(self, description: str, format_type: str = "json", size: int = 10) -> Dict[str, Any]:
        """
        Fallback dataset creation when OpenAI is not available
        
        Args:
            description: Description of the dataset
            format_type: Format type (json, csv, etc.)
            size: Number of items in the dataset
            
        Returns:
            Dictionary with basic sample dataset
        """
        import random
        import string
        import datetime as dt
        
        # Parse description to identify data types and structure
        description_lower = description.lower()
        
        # Default fields for common dataset types
        dataset_types = {
            "user": {
                "fields": ["id", "name", "email", "age", "signup_date"],
                "types": ["int", "name", "email", "int_range", "date"]
            },
            "product": {
                "fields": ["id", "name", "description", "price", "category", "in_stock"],
                "types": ["int", "short_text", "text", "price", "category", "boolean"]
            },
            "transaction": {
                "fields": ["id", "user_id", "product_id", "amount", "date", "status"],
                "types": ["int", "int", "int", "price", "date", "status"]
            },
            "comment": {
                "fields": ["id", "user_id", "content", "date", "likes"],
                "types": ["int", "int", "text", "date", "int"]
            },
            "weather": {
                "fields": ["id", "date", "location", "temperature", "humidity", "description"],
                "types": ["int", "date", "location", "temperature", "percentage", "weather"]
            }
        }
        
        # Default values generators
        generators = {
            "int": lambda i: i + 1,
            "int_range": lambda i: random.randint(18, 65),
            "float": lambda i: round(random.uniform(0, 100), 2),
            "name": lambda i: f"{random.choice(['John', 'Jane', 'Alex', 'Sam', 'Chris', 'Pat', 'Jordan', 'Taylor', 'Morgan', 'Casey'])} {random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Martinez', 'Wilson'])}",
            "email": lambda i: f"{random.choice(['john', 'jane', 'alex', 'sam', 'chris', 'pat'])}.{random.choice(['smith', 'johnson', 'brown'])}{random.randint(1, 999)}@{random.choice(['gmail.com', 'yahoo.com', 'outlook.com', 'example.com'])}",
            "short_text": lambda i: random.choice(["Basic", "Premium", "Deluxe", "Standard", "Professional", "Ultimate"]) + " " + random.choice(["Product", "Item", "Package", "Kit", "Solution", "Service"]),
            "text": lambda i: "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
            "date": lambda i: (dt.datetime.now() - dt.timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d"),
            "price": lambda i: round(random.uniform(9.99, 99.99), 2),
            "category": lambda i: random.choice(["Electronics", "Clothing", "Books", "Home & Garden", "Food", "Health", "Beauty", "Sports", "Toys", "Automotive"]),
            "boolean": lambda i: random.choice([True, False]),
            "status": lambda i: random.choice(["pending", "completed", "failed", "processing"]),
            "location": lambda i: random.choice(["New York", "London", "Tokyo", "Paris", "Berlin", "Sydney", "Toronto", "Mumbai", "Beijing", "Rio de Janeiro"]),
            "temperature": lambda i: round(random.uniform(-10, 40), 1),
            "percentage": lambda i: random.randint(0, 100),
            "weather": lambda i: random.choice(["Sunny", "Cloudy", "Rainy", "Snowy", "Windy", "Foggy", "Thunderstorm", "Clear", "Partly cloudy", "Overcast"])
        }
        
        # Determine dataset type based on description
        dataset_type = "user"  # default
        for dtype, keywords in {
            "user": ["user", "person", "people", "customer", "profile"],
            "product": ["product", "item", "merchandise", "goods", "inventory"],
            "transaction": ["transaction", "order", "purchase", "sale", "payment"],
            "comment": ["comment", "review", "feedback", "rating", "message"],
            "weather": ["weather", "climate", "forecast", "temperature", "meteorological"]
        }.items():
            if any(keyword in description_lower for keyword in keywords):
                dataset_type = dtype
                break
        
        # Generate dataset
        fields = dataset_types[dataset_type]["fields"]
        types = dataset_types[dataset_type]["types"]
        
        if format_type.lower() == "json":
            dataset = []
            for i in range(size):
                item = {}
                for field, field_type in zip(fields, types):
                    item[field] = generators.get(field_type, generators["short_text"])(i)
                dataset.append(item)
            
            result = dataset
            
        elif format_type.lower() == "csv":
            # Generate CSV content
            header = ",".join(fields)
            rows = []
            for i in range(size):
                row = []
                for field_type in types:
                    value = generators.get(field_type, generators["short_text"])(i)
                    # Format value for CSV
                    if isinstance(value, str):
                        value = f'"{value}"'
                    elif isinstance(value, bool):
                        value = str(value).lower()
                    else:
                        value = str(value)
                    row.append(value)
                rows.append(",".join(row))
            
            result = header + "\n" + "\n".join(rows)
            
        else:
            # Default to JSON if format not supported
            dataset = []
            for i in range(size):
                item = {}
                for field, field_type in zip(fields, types):
                    item[field] = generators.get(field_type, generators["short_text"])(i)
                dataset.append(item)
            
            result = dataset
        
        return {
            "status": "success",
            "format": format_type,
            "size": size,
            "dataset": result,
            "note": f"Generated using THOR's basic data generator (OpenAI integration unavailable). This is a sample {dataset_type} dataset."
        }
    
    def network_scan(self, target_description: str) -> Dict[str, Any]:
        """
        Generate network scanning code
        
        Args:
            target_description: Description of the network task
            
        Returns:
            Dictionary with generated code and explanation
        """
        # If no AI providers are available, use the built-in fallback
        if not self.thor_ai and not self.anthropic_ai:
            return self._generate_fallback_network_scan(target_description)
        
        # Try OpenAI first if available
        if self.thor_ai:
            try:
                result = self.thor_ai.network_scan(target_description)
                return {
                    "status": "success",
                    "result": result,
                    "provider": "openai"
                }
            except Exception as e:
                logger.error(f"OpenAI network scan error: {e}")
                logger.info("Attempting to use Anthropic as fallback")
                
                # If Anthropic is available as fallback
                if self.anthropic_ai:
                    try:
                        result = self.anthropic_ai.network_scan(target_description)
                        return {
                            "status": "success",
                            "result": result,
                            "provider": "anthropic"
                        }
                    except Exception as e2:
                        logger.error(f"Anthropic fallback failed: {e2}")
                
                # If both fail or Anthropic isn't available, use built-in fallback
                logger.info("Falling back to basic network scan script")
                return self._generate_fallback_network_scan(target_description)
        
        # If only Anthropic is available
        elif self.anthropic_ai:
            try:
                result = self.anthropic_ai.network_scan(target_description)
                return {
                    "status": "success",
                    "result": result,
                    "provider": "anthropic"
                }
            except Exception as e:
                logger.error(f"Anthropic network scan error: {e}")
                logger.info("Falling back to basic network scan script")
                return self._generate_fallback_network_scan(target_description)
                
        # This shouldn't be reachable given the first if statement, but added to satisfy type checker
        return self._generate_fallback_network_scan(target_description)
            
    def _generate_fallback_network_scan(self, target_description: str) -> Dict[str, Any]:
        """
        Fallback network scan script generation when OpenAI is not available
        
        Args:
            target_description: Description of the network task
            
        Returns:
            Dictionary with basic network scan script
        """
        description_lower = target_description.lower()
        
        port_scanner_script = """#!/usr/bin/env python3
# Basic Port Scanner - For educational purposes only
# Use responsibly and only on networks you own or have permission to scan

import socket
import ipaddress
import argparse
from datetime import datetime
import sys
import time

def scan_port(ip, port, timeout=1):
    # Create a socket object
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    
    try:
        # Try to connect to the port
        result = s.connect_ex((ip, port))
        if result == 0:
            try:
                # Try to identify the service
                service = socket.getservbyport(port)
            except:
                service = "unknown"
            return True, service
        return False, None
    except socket.error:
        return False, None
    finally:
        s.close()

def scan_target(target, ports, verbose=True):
    try:
        # Try to parse as IP address or network
        try:
            # Check if it's a network range (CIDR notation)
            if '/' in target:
                network = ipaddress.ip_network(target, strict=False)
                targets = [str(ip) for ip in network.hosts()]
            else:
                # It's a single IP
                ipaddress.ip_address(target)
                targets = [target]
        except ValueError:
            # Not an IP, try to resolve hostname
            try:
                ip = socket.gethostbyname(target)
                targets = [ip]
            except socket.gaierror:
                print(f"Error: Could not resolve hostname {target}")
                return
    
        for ip in targets:
            if verbose:
                print(f"\\nScanning {ip}...")
                print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                start_time = time.time()
            
            open_ports = []
            
            for port in ports:
                if verbose and len(targets) == 1:
                    sys.stdout.write(f"\\rScanning port {port}/{ports[-1]}...")
                    sys.stdout.flush()
                
                is_open, service = scan_port(ip, port)
                
                if is_open:
                    open_ports.append((port, service))
            
            if verbose:
                elapsed = time.time() - start_time
                print(f"\\nScan completed in {elapsed:.2f} seconds")
                
            if open_ports:
                print(f"\\nOpen ports on {ip}:")
                print("PORT\\tSTATE\\tSERVICE")
                for port, service in open_ports:
                    print(f"{port}\\topen\\t{service}")
            elif verbose:
                print(f"\\nNo open ports found on {ip}")
    
    except KeyboardInterrupt:
        print("\\nScan interrupted by user")
    except Exception as e:
        print(f"Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Simple Port Scanner")
    parser.add_argument("target", help="Target IP, hostname, or network (CIDR notation)")
    parser.add_argument("-p", "--ports", default="1-1024", help="Port range to scan (e.g., '1-1024' or '22,80,443')")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Parse port argument
    ports_to_scan = []
    if "," in args.ports:
        # Comma-separated list of ports
        ports_to_scan = [int(p.strip()) for p in args.ports.split(",")]
    elif "-" in args.ports:
        # Port range
        start, end = map(int, args.ports.split("-"))
        ports_to_scan = list(range(start, end + 1))
    else:
        # Single port
        ports_to_scan = [int(args.ports)]
    
    scan_target(args.target, ports_to_scan, args.verbose)

if __name__ == "__main__":
    print("Simple Port Scanner")
    print("For educational purposes only. Use responsibly.")
    main()
"""

        packet_capture_script = """#!/usr/bin/env python3
# Basic Packet Capture Script - For educational purposes only
# Use responsibly and only on networks you own or have permission to monitor

import argparse
from datetime import datetime
import sys
import os

try:
    from scapy.all import sniff, wrpcap, IP, TCP, UDP
    HAS_SCAPY = True
except ImportError:
    HAS_SCAPY = False
    print("Warning: Scapy is not installed. This script requires Scapy.")
    print("Install with: pip install scapy")
    print("Note: Scapy might require additional system dependencies.")

class PacketCapture:
    def __init__(self, interface=None, count=None, timeout=None, filter_str=None, output_file=None):
        self.interface = interface
        self.count = count
        self.timeout = timeout
        self.filter_str = filter_str
        self.output_file = output_file
        self.packets = []
        self.start_time = None
        self.end_time = None
        
    def packet_callback(self, packet):
        # Add packet to our list
        self.packets.append(packet)
        
        # Print packet info
        packet_info = f"[{len(self.packets)}] "
        
        if IP in packet:
            src_ip = packet[IP].src
            dst_ip = packet[IP].dst
            proto = packet[IP].proto
            packet_info += f"{src_ip} -> {dst_ip} "
            
            if TCP in packet:
                src_port = packet[TCP].sport
                dst_port = packet[TCP].dport
                flags = packet[TCP].flags
                packet_info += f"TCP {src_port} -> {dst_port} [Flags: {flags}]"
            elif UDP in packet:
                src_port = packet[UDP].sport
                dst_port = packet[UDP].dport
                packet_info += f"UDP {src_port} -> {dst_port}"
            else:
                packet_info += f"Proto: {proto}"
        
        print(packet_info)
        
        # Flush output to ensure real-time display
        sys.stdout.flush()
        
    def start_capture(self):
        if not HAS_SCAPY:
            return False
            
        try:
            print(f"Starting packet capture on {self.interface if self.interface else 'default interface'}")
            if self.filter_str:
                print(f"Filter: {self.filter_str}")
            print(f"Duration: {'Unlimited' if not self.timeout else f'{self.timeout} seconds'}")
            print(f"Count limit: {'Unlimited' if not self.count else self.count}")
            print("Press Ctrl+C to stop the capture")
            print("-" * 60)
            
            self.start_time = datetime.now()
            
            # Start packet capture
            sniff(
                iface=self.interface,
                prn=self.packet_callback,
                filter=self.filter_str,
                count=self.count,
                timeout=self.timeout,
                store=0  # Don't store packets in memory (we're handling them in the callback)
            )
            
            return True
            
        except KeyboardInterrupt:
            print("\\nCapture stopped by user")
            return True
        except Exception as e:
            print(f"Error during capture: {e}")
            return False
        finally:
            self.end_time = datetime.now()
            
    def save_pcap(self):
        if not self.packets:
            print("No packets captured")
            return False
            
        if not self.output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_file = f"capture_{timestamp}.pcap"
            
        try:
            wrpcap(self.output_file, self.packets)
            print(f"Saved {len(self.packets)} packets to {self.output_file}")
            return True
        except Exception as e:
            print(f"Error saving PCAP file: {e}")
            return False
            
    def print_summary(self):
        if not self.start_time or not self.end_time:
            return
            
        duration = (self.end_time - self.start_time).total_seconds()
        print("\\nCapture Summary:")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Packets captured: {len(self.packets)}")
        if len(self.packets) > 0:
            print(f"Packets per second: {len(self.packets)/duration:.2f}")

def main():
    parser = argparse.ArgumentParser(description="Simple Packet Capture Tool")
    parser.add_argument("-i", "--interface", help="Network interface to capture on")
    parser.add_argument("-c", "--count", type=int, help="Stop after capturing COUNT packets")
    parser.add_argument("-t", "--timeout", type=int, help="Stop after TIMEOUT seconds")
    parser.add_argument("-f", "--filter", help="BPF filter expression")
    parser.add_argument("-w", "--write", help="Write packets to PCAP file")
    parser.add_argument("--tcp", action="store_true", help="Capture only TCP traffic")
    parser.add_argument("--udp", action="store_true", help="Capture only UDP traffic")
    parser.add_argument("--icmp", action="store_true", help="Capture only ICMP traffic")
    parser.add_argument("--port", type=int, help="Capture traffic on specific port")
    
    args = parser.parse_args()
    
    # Build filter string
    filter_str = ""
    if args.tcp:
        filter_str = "tcp"
    elif args.udp:
        filter_str = "udp"
    elif args.icmp:
        filter_str = "icmp"
        
    if args.port:
        if filter_str:
            filter_str += f" and port {args.port}"
        else:
            filter_str = f"port {args.port}"
    
    # If custom filter is provided, it overrides the simplified options
    if args.filter:
        filter_str = args.filter
    
    # Create and start packet capture
    capture = PacketCapture(
        interface=args.interface,
        count=args.count,
        timeout=args.timeout,
        filter_str=filter_str,
        output_file=args.write
    )
    
    if capture.start_capture():
        capture.print_summary()
        if args.write or len(capture.packets) > 0:
            capture.save_pcap()

if __name__ == "__main__":
    # Check if running as root (required for packet capture on most systems)
    if os.name != "nt" and os.geteuid() != 0:
        print("Warning: Packet capture usually requires root privileges")
        print("Consider running this script with sudo")
        
    print("Simple Packet Capture Tool")
    print("For educational purposes only. Use responsibly.")
    main()
"""

        network_monitor_script = """#!/usr/bin/env python3
# Basic Network Monitor - For educational purposes only
# Use responsibly and only on networks you own or have permission to monitor

import socket
import time
import datetime
import argparse
import subprocess
import platform
import os
import sys
import signal
import threading
from collections import defaultdict

# Global variables
running = True
hosts_status = {}
traffic_stats = defaultdict(lambda: {'rx_bytes': 0, 'tx_bytes': 0, 'rx_packets': 0, 'tx_packets': 0})
lock = threading.Lock()

def signal_handler(sig, frame):
    global running
    print("\\nStopping network monitor...")
    running = False

def ping(host, timeout=1):
    # Returns True if host responds to a ping request
    # Check platform for ping command format
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    timeout_param = '-w' if platform.system().lower() == 'windows' else '-W'
    
    # Build the command
    command = ['ping', param, '1', timeout_param, str(timeout), host]
    
    try:
        return subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
    except:
        return False

def monitor_hosts(hosts, interval):
    # Monitor a list of hosts with ping
    global running, hosts_status
    
    print(f"Starting host monitoring for {len(hosts)} hosts (interval: {interval}s)")
    
    while running:
        for host in hosts:
            is_up = ping(host)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with lock:
                # Check if status has changed
                if host in hosts_status and hosts_status[host]['status'] != is_up:
                    status_change = f"{'UP' if is_up else 'DOWN'} (was {'UP' if hosts_status[host]['status'] else 'DOWN'})"
                else:
                    status_change = 'UP' if is_up else 'DOWN'
                
                hosts_status[host] = {
                    'status': is_up,
                    'timestamp': timestamp,
                    'status_change': status_change
                }
                
            print(f"[{timestamp}] Host {host}: {status_change}")
        
        # Wait for the specified interval
        for _ in range(interval):
            if not running:
                break
            time.sleep(1)

def get_interface_stats(interface):
    # Get the current network interface statistics
    if platform.system().lower() == 'linux':
        try:
            with open(f"/sys/class/net/{interface}/statistics/rx_bytes", 'r') as f:
                rx_bytes = int(f.read().strip())
            with open(f"/sys/class/net/{interface}/statistics/tx_bytes", 'r') as f:
                tx_bytes = int(f.read().strip())
            with open(f"/sys/class/net/{interface}/statistics/rx_packets", 'r') as f:
                rx_packets = int(f.read().strip())
            with open(f"/sys/class/net/{interface}/statistics/tx_packets", 'r') as f:
                tx_packets = int(f.read().strip())
                
            return {
                'rx_bytes': rx_bytes,
                'tx_bytes': tx_bytes,
                'rx_packets': rx_packets,
                'tx_packets': tx_packets
            }
        except:
            return None
    else:
        # Not implemented for other platforms
        return None

def monitor_traffic(interfaces, interval):
    # Monitor traffic on specified interfaces
    global running, traffic_stats
    
    if platform.system().lower() != 'linux':
        print("Traffic monitoring is currently only supported on Linux")
        return
    
    print(f"Starting traffic monitoring for {', '.join(interfaces)} (interval: {interval}s)")
    
    # Initialize stats
    for interface in interfaces:
        stats = get_interface_stats(interface)
        if stats:
            with lock:
                traffic_stats[interface] = stats
    
    while running:
        time.sleep(interval)
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] Traffic statistics:")
        
        for interface in interfaces:
            new_stats = get_interface_stats(interface)
            if not new_stats:
                continue
                
            with lock:
                old_stats = traffic_stats[interface]
                
                # Calculate differences
                rx_bytes_diff = new_stats['rx_bytes'] - old_stats['rx_bytes']
                tx_bytes_diff = new_stats['tx_bytes'] - old_stats['tx_bytes']
                rx_packets_diff = new_stats['rx_packets'] - old_stats['rx_packets']
                tx_packets_diff = new_stats['tx_packets'] - old_stats['tx_packets']
                
                # Update stored stats
                traffic_stats[interface] = new_stats
            
            # Convert to KB/s
            rx_rate = rx_bytes_diff / interval / 1024
            tx_rate = tx_bytes_diff / interval / 1024
            
            print(f"  {interface}: RX: {rx_rate:.2f} KB/s ({rx_packets_diff} pkts), TX: {tx_rate:.2f} KB/s ({tx_packets_diff} pkts)")

def port_scan(host, ports):
    # Quick scan of common ports on a host
    open_ports = []
    
    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            service = "unknown"
            try:
                service = socket.getservbyport(port)
            except:
                pass
            open_ports.append((port, service))
    
    return open_ports

def main():
    parser = argparse.ArgumentParser(description="Simple Network Monitor")
    parser.add_argument("-H", "--hosts", help="Comma-separated list of hosts to monitor")
    parser.add_argument("-i", "--interfaces", help="Comma-separated list of interfaces to monitor")
    parser.add_argument("-t", "--interval", type=int, default=5, help="Monitoring interval in seconds")
    parser.add_argument("-p", "--ports", help="Comma-separated list of ports to check")
    parser.add_argument("-s", "--scan", help="Host to perform a port scan on")
    
    args = parser.parse_args()
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # One-time port scan
    if args.scan:
        print(f"Performing port scan on {args.scan}...")
        ports = [21, 22, 23, 25, 53, 80, 110, 443, 3306, 3389, 5900, 8080]
        if args.ports:
            ports = [int(p.strip()) for p in args.ports.split(",")]
        
        open_ports = port_scan(args.scan, ports)
        
        if open_ports:
            print(f"Open ports on {args.scan}:")
            print("PORT\\tSERVICE")
            for port, service in open_ports:
                print(f"{port}\\t{service}")
        else:
            print(f"No open ports found on {args.scan}")
        
        return
    
    threads = []
    
    # Start host monitoring thread
    if args.hosts:
        hosts = [h.strip() for h in args.hosts.split(",")]
        host_thread = threading.Thread(target=monitor_hosts, args=(hosts, args.interval))
        host_thread.daemon = True
        host_thread.start()
        threads.append(host_thread)
    
    # Start traffic monitoring thread
    if args.interfaces:
        interfaces = [i.strip() for i in args.interfaces.split(",")]
        traffic_thread = threading.Thread(target=monitor_traffic, args=(interfaces, args.interval))
        traffic_thread.daemon = True
        traffic_thread.start()
        threads.append(traffic_thread)
    
    if not threads:
        parser.print_help()
        return
    
    print("Network monitor running. Press Ctrl+C to stop.")
    
    try:
        # Keep the main thread alive
        while running and any(t.is_alive() for t in threads):
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    
    print("Network monitor stopped.")

if __name__ == "__main__":
    print("Simple Network Monitor")
    print("For educational purposes only. Use responsibly.")
    main()
"""
        
        # Determine which script to use based on description
        script = port_scanner_script
        explanation = "This script is a basic port scanner that checks for open ports on a target IP, hostname, or network range."
        
        if "monitor" in description_lower or "track" in description_lower or "watch" in description_lower:
            script = network_monitor_script
            explanation = "This script is a basic network monitoring tool that provides host monitoring, traffic monitoring, and port scanning capabilities."
        elif "packet" in description_lower or "capture" in description_lower or "sniff" in description_lower:
            script = packet_capture_script
            explanation = "This script is a basic packet capture tool that captures and analyzes network packets using Scapy."
        
        return {
            "status": "success",
            "result": {
                "script": script,
                "explanation": explanation + "\n\nNote: Generated using THOR's built-in templates (OpenAI integration unavailable)."
            }
        }
    
    def suggest_improvements(self) -> Dict[str, Any]:
        """
        Suggest self-improvements for THOR
        
        Returns:
            Dictionary with improvement suggestions
        """
        # If no AI providers are available, use the built-in fallback
        if not self.thor_ai and not self.anthropic_ai:
            return self._generate_fallback_improvements()
        
        system_description = f"THOR AI System Version {self.model_info['version']}\n"
        system_description += f"Capabilities: {', '.join(self.model_info['capabilities'])}\n"
        
        # Try OpenAI first if available
        if self.thor_ai:
            try:
                suggestions = self.thor_ai.suggest_improvements(system_description)
                return {
                    "status": "success",
                    "suggestions": suggestions,
                    "provider": "openai"
                }
            except Exception as e:
                logger.error(f"OpenAI improvements suggestion error: {e}")
                logger.info("Attempting to use Anthropic as fallback")
                
                # If Anthropic is available as fallback
                if self.anthropic_ai:
                    try:
                        result = self.anthropic_ai.suggest_improvements()
                        return {
                            "status": "success",
                            "suggestions": result.get("suggestions", "No suggestions provided"),
                            "provider": "anthropic"
                        }
                    except Exception as e2:
                        logger.error(f"Anthropic fallback failed: {e2}")
                
                # If both fail or Anthropic isn't available, use built-in fallback
                logger.info("Falling back to basic improvement suggestions")
                return self._generate_fallback_improvements()
        
        # If only Anthropic is available
        elif self.anthropic_ai:
            try:
                result = self.anthropic_ai.suggest_improvements()
                return {
                    "status": "success",
                    "suggestions": result.get("suggestions", "No suggestions provided"),
                    "provider": "anthropic"
                }
            except Exception as e:
                logger.error(f"Anthropic improvement suggestion error: {e}")
                logger.info("Falling back to basic improvement suggestions")
                return self._generate_fallback_improvements()
                
        # This shouldn't be reachable given the first if statement, but added to satisfy type checker
        return self._generate_fallback_improvements()
            
    def _generate_fallback_improvements(self) -> Dict[str, Any]:
        """
        Fallback improvement suggestions when OpenAI is not available
        
        Returns:
            Dictionary with basic improvement suggestions
        """
        # Generate generic improvement suggestions
        suggestions = [
            {
                "title": "Implement Natural Language Processing",
                "description": "Integrate a natural language processing library to improve understanding of user queries and provide more contextual responses.",
                "priority": "high",
                "implementation": "Consider using spaCy or NLTK for NLP capabilities:\n\npip install spacy\npython -m spacy download en_core_web_sm\n\n# Then in code\nimport spacy\nnlp = spacy.load('en_core_web_sm')\n\ndef analyze_text(text):\n    doc = nlp(text)\n    # Extract entities, intents, etc.\n    return {\"entities\": [(ent.text, ent.label_) for ent in doc.ents]}"
            },
            {
                "title": "Add Voice Input and Output",
                "description": "Enhance user interaction by adding voice recognition and text-to-speech capabilities.",
                "priority": "medium",
                "implementation": "Use libraries like SpeechRecognition and pyttsx3:\n\npip install SpeechRecognition pyttsx3\n\n# Example implementation\nimport speech_recognition as sr\nimport pyttsx3\n\ndef listen():\n    recognizer = sr.Recognizer()\n    with sr.Microphone() as source:\n        audio = recognizer.listen(source)\n        try:\n            return recognizer.recognize_google(audio)\n        except:\n            return None\n            \ndef speak(text):\n    engine = pyttsx3.init()\n    engine.say(text)\n    engine.runAndWait()"
            },
            {
                "title": "Implement Memory System",
                "description": "Create a more sophisticated memory system to remember past interactions with users and learn from them.",
                "priority": "high",
                "implementation": "Create a database-backed memory system:\n\nfrom sqlalchemy import create_engine, Column, Integer, String, Text, DateTime\nfrom sqlalchemy.ext.declarative import declarative_base\nfrom sqlalchemy.orm import sessionmaker\nimport datetime\n\nBase = declarative_base()\n\nclass Memory(Base):\n    __tablename__ = 'memories'\n    id = Column(Integer, primary_key=True)\n    user_id = Column(String(50))\n    context = Column(String(100))\n    information = Column(Text)\n    created_at = Column(DateTime, default=datetime.datetime.utcnow)\n    \n# Then create functions to store and retrieve memories"
            },
            {
                "title": "Add Multi-Model Support",
                "description": "Expand THOR to support multiple underlying AI models that can be switched based on the task or user preference.",
                "priority": "medium",
                "implementation": "Implement a model factory and adapter pattern:\n\nclass ModelFactory:\n    @staticmethod\n    def get_model(model_name):\n        if model_name == \"gpt4\":\n            return GPT4Model()\n        elif model_name == \"llama\":\n            return LlamaModel()\n        # Add more models\n        else:\n            return DefaultModel()\n            \nclass BaseModel:\n    def generate(self, prompt):\n        raise NotImplementedError()\n        \nclass GPT4Model(BaseModel):\n    def generate(self, prompt):\n        # Implementation for GPT-4\n        pass"
            },
            {
                "title": "Create Administration Dashboard",
                "description": "Develop a web-based administration dashboard where users can monitor THOR's performance, view logs, and configure settings.",
                "priority": "low",
                "implementation": "Use a framework like Flask and a frontend library like Bootstrap:\n\nfrom flask import Flask, render_template\n\napp = Flask(__name__)\n\n@app.route('/admin')\ndef admin_dashboard():\n    # Get system stats\n    stats = get_system_stats()\n    return render_template('admin.html', stats=stats)\n    \n# Create admin.html with Bootstrap for styling"
            },
            {
                "title": "Implement Sentiment Analysis",
                "description": "Add ability to detect user sentiment in messages to adjust responses accordingly.",
                "priority": "medium",
                "implementation": "Use a sentiment analysis library like TextBlob:\n\npip install textblob\n\nfrom textblob import TextBlob\n\ndef analyze_sentiment(text):\n    blob = TextBlob(text)\n    polarity = blob.sentiment.polarity  # -1 to 1\n    subjectivity = blob.sentiment.subjectivity  # 0 to 1\n    \n    if polarity > 0.3:\n        sentiment = \"positive\"\n    elif polarity < -0.3:\n        sentiment = \"negative\"\n    else:\n        sentiment = \"neutral\"\n        \n    return {\"sentiment\": sentiment, \"polarity\": polarity, \"subjectivity\": subjectivity}"
            },
            {
                "title": "Add Learning Capability",
                "description": "Implement a reinforcement learning system that allows THOR to improve based on user feedback.",
                "priority": "high",
                "implementation": "Create a feedback loop system:\n\nclass FeedbackSystem:\n    def __init__(self):\n        self.response_ratings = {}\n        \n    def record_feedback(self, response_id, rating):\n        self.response_ratings[response_id] = rating\n        self.update_weights(response_id, rating)\n        \n    def update_weights(self, response_id, rating):\n        # Update model weights based on feedback\n        pass\n        \n    def generate_improved_response(self, similar_query):\n        # Use past feedback to generate better responses\n        pass"
            }
        ]
        
        return {
            "status": "success",
            "suggestions": suggestions,
            "note": "Generated using THOR's built-in suggestions (OpenAI integration unavailable)."
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
