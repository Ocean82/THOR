import re
import logging
from typing import Dict, List, Optional, Any, Tuple
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class NLPProcessor:
    """
    Handles natural language processing tasks including text analysis,
    content filtering, and conversation management
    """
    
    def __init__(self):
        """Initialize the NLP processor with required resources"""
        try:
            # Initialize NLTK resources
            self.stopwords = set(stopwords.words('english'))
            
            # Unsafe content patterns
            self.unsafe_patterns = [
                r'(hack|exploit|attack|compromise)\s+(system|server|computer|network)',
                r'(illegal|unlawful)\s+(activity|operation|action)',
                r'(bypass|circumvent)\s+(security|protection|filter)',
                r'(steal|obtain)\s+(password|credentials|sensitive\s+data)',
                r'(launch|execute)\s+(malware|virus|ransomware)',
            ]
            
            logger.info("NLP Processor initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing NLP Processor: {e}")
            # Create empty stopwords if NLTK failed
            self.stopwords = set()
            
    def process_text(self, text: str) -> str:
        """
        Process text with basic NLP operations
        
        Args:
            text: Input text to process
            
        Returns:
            Processed text
        """
        try:
            # Basic text cleaning
            processed_text = text.strip()
            
            # Remove extra whitespace
            processed_text = re.sub(r'\s+', ' ', processed_text)
            
            return processed_text
            
        except Exception as e:
            logger.error(f"Error processing text: {e}")
            return text  # Return original text if processing fails
    
    def analyze_intent(self, text: str) -> Dict[str, Any]:
        """
        Analyze the user's intent from their input
        
        Args:
            text: User input text
            
        Returns:
            Dictionary containing intent classification
        """
        try:
            text_lower = text.lower()
            
            # Basic intent detection using keyword matching
            intents = {
                "greeting": any(word in text_lower for word in ["hello", "hi", "hey", "greetings"]),
                "question": '?' in text or any(word in text_lower for word in ["what", "why", "how", "when", "where", "who"]),
                "command": any(word in text_lower for word in ["do", "execute", "run", "perform", "download", "clone", "modify"]),
                "farewell": any(word in text_lower for word in ["bye", "goodbye", "exit", "quit", "end"]),
                "help": "help" in text_lower or "assist" in text_lower,
                "settings": any(word in text_lower for word in ["setting", "configure", "preference", "option"])
            }
            
            # Determine primary intent
            primary_intent = max(intents.items(), key=lambda x: x[1])[0] if any(intents.values()) else "general"
            
            return {
                "primary_intent": primary_intent,
                "intents": intents,
                "confidence": 0.7  # Placeholder for more sophisticated intent detection
            }
            
        except Exception as e:
            logger.error(f"Error analyzing intent: {e}")
            return {"primary_intent": "general", "intents": {}, "confidence": 0.0}
    
    def filter_unsafe_content(self, text: str) -> str:
        """
        Filter potentially unsafe content from text
        
        Args:
            text: Text to filter
            
        Returns:
            Filtered text
        """
        try:
            # Check for unsafe patterns
            for pattern in self.unsafe_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return "I apologize, but I cannot provide that information or perform that action due to safety constraints."
            
            return text
            
        except Exception as e:
            logger.error(f"Error filtering content: {e}")
            return "I apologize, but I encountered an error processing your request."
    
    def extract_keywords(self, text: str) -> List[str]:
        """
        Extract important keywords from text
        
        Args:
            text: Input text
            
        Returns:
            List of keywords
        """
        try:
            # Tokenize text
            tokens = word_tokenize(text.lower())
            
            # Remove stopwords and non-alphabetic tokens
            keywords = [word for word in tokens if word.isalpha() and word not in self.stopwords]
            
            return keywords[:10]  # Return top 10 keywords
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []
            
    def summarize_conversation(self, messages: List[Dict[str, Any]]) -> str:
        """
        Generate a brief summary of the conversation
        
        Args:
            messages: List of conversation messages
            
        Returns:
            Summary text
        """
        try:
            if not messages:
                return "No conversation to summarize."
                
            # Extract just the content from messages
            contents = [msg.get('content', '') for msg in messages]
            
            # Join all content with spaces
            full_text = ' '.join(contents)
            
            # Get key terms from the conversation
            keywords = self.extract_keywords(full_text)
            
            # Create a simple summary based on conversation length
            if len(messages) <= 3:
                return f"Brief conversation about {', '.join(keywords[:3])}."
            else:
                return f"Extended conversation covering {', '.join(keywords[:5])}."
                
        except Exception as e:
            logger.error(f"Error summarizing conversation: {e}")
            return "Unable to summarize conversation."
