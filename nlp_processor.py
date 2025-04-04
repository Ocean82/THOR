import re
import logging
from typing import Dict, List, Optional, Any, Tuple
import string

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class NLPProcessor:
    """
    Handles natural language processing tasks including text analysis,
    content filtering, and conversation management
    Simplified version without external NLP libraries
    """
    
    def __init__(self):
        """Initialize the NLP processor with required resources"""
        # Common English stopwords
        self.stopwords = {
            'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 
            'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 
            'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 
            'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 
            'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 
            'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 
            'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 
            'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 
            'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 
            'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 
            'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 
            'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 
            'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 
            's', 't', 'can', 'will', 'just', 'don', 'should', 'now'
        }
        
        # Unsafe content patterns
        self.unsafe_patterns = [
            r'(hack|exploit|attack|compromise)\s+(system|server|computer|network)',
            r'(illegal|unlawful)\s+(activity|operation|action)',
            r'(bypass|circumvent)\s+(security|protection|filter)',
            r'(steal|obtain)\s+(password|credentials|sensitive\s+data)',
            r'(launch|execute)\s+(malware|virus|ransomware)',
        ]
        
        logger.info("Simplified NLP Processor initialized successfully")
            
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
            primary_intent = "general"
            max_score = 0
            for intent, score in intents.items():
                if score and score > max_score:
                    primary_intent = intent
                    max_score = score
            
            return {
                "primary_intent": primary_intent,
                "intents": intents,
                "confidence": 0.7 if max_score else 0.3  # Simple confidence score
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
            # Simple tokenization - split by whitespace and remove punctuation
            text = text.lower()
            for char in string.punctuation:
                text = text.replace(char, ' ')
            tokens = text.split()
            
            # Remove stopwords and short tokens
            keywords = [word for word in tokens if word not in self.stopwords and len(word) > 3]
            
            # Count occurrences and sort by frequency
            keyword_counts = {}
            for word in keywords:
                if word in keyword_counts:
                    keyword_counts[word] += 1
                else:
                    keyword_counts[word] = 1
            
            # Sort by count (descending)
            sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
            
            # Return just the words (not counts)
            return [word for word, count in sorted_keywords[:10]]
            
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
                keyword_str = ', '.join(keywords[:3]) if keywords else "various topics"
                return f"Brief conversation about {keyword_str}."
            else:
                keyword_str = ', '.join(keywords[:5]) if keywords else "various topics"
                return f"Extended conversation covering {keyword_str}."
                
        except Exception as e:
            logger.error(f"Error summarizing conversation: {e}")
            return "Unable to summarize conversation."
