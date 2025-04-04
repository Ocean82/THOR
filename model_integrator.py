import os
import logging
import requests
from typing import Dict, List, Optional, Any
import tempfile
import shutil
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ModelIntegrator:
    """
    Handles downloading, caching, and integrating external models
    from sources like Hugging Face and GitHub
    """
    
    def __init__(self, cache_dir: str = None):
        """
        Initialize model integrator with cache directory
        
        Args:
            cache_dir: Directory to cache downloaded models
        """
        # Set cache directory
        if cache_dir:
            self.cache_dir = cache_dir
        else:
            self.cache_dir = os.path.join(tempfile.gettempdir(), "ai_model_cache")
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Track cached models
        self.cached_models = self._scan_cache()
        
        logger.info(f"Model Integrator initialized with cache at {self.cache_dir}")

    def _scan_cache(self) -> Dict[str, str]:
        """
        Scan cache directory for already downloaded models
        
        Returns:
            Dictionary mapping model names to their cache paths
        """
        cached_models = {}
        try:
            for item in os.listdir(self.cache_dir):
                item_path = os.path.join(self.cache_dir, item)
                if os.path.isdir(item_path):
                    cached_models[item] = item_path
            
            logger.info(f"Found {len(cached_models)} models in cache")
            return cached_models
            
        except Exception as e:
            logger.error(f"Error scanning cache: {e}")
            return {}
    
    def get_model_path(self, model_name: str) -> str:
        """
        Get path to a model, downloading it if not in cache
        
        Args:
            model_name: Name of the model to retrieve
            
        Returns:
            Path to the model directory
        """
        # Check if model is in cache
        if model_name in self.cached_models:
            logger.info(f"Model {model_name} found in cache")
            return self.cached_models[model_name]
        
        # If not in cache, download from Hugging Face
        try:
            logger.info(f"Downloading model {model_name} from Hugging Face")
            from transformers import AutoModel, AutoTokenizer
            
            # Create model directory
            model_path = os.path.join(self.cache_dir, model_name)
            os.makedirs(model_path, exist_ok=True)
            
            # Download model and tokenizer
            model = AutoModel.from_pretrained(model_name)
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            # Save model and tokenizer to cache
            model.save_pretrained(model_path)
            tokenizer.save_pretrained(model_path)
            
            # Update cached models
            self.cached_models[model_name] = model_path
            
            logger.info(f"Model {model_name} downloaded and cached successfully")
            return model_path
            
        except Exception as e:
            logger.error(f"Error downloading model {model_name}: {e}")
            # If download fails, use a default model
            return model_name  # Return the name, which Hugging Face will attempt to download directly
    
    def download_from_github(self, repo_url: str, model_name: str) -> Optional[str]:
        """
        Download a model from a GitHub repository
        
        Args:
            repo_url: URL of the GitHub repository
            model_name: Name to save the model under
            
        Returns:
            Path to downloaded model or None on failure
        """
        try:
            logger.info(f"Attempting to download from GitHub: {repo_url}")
            
            # Extract username and repo name from URL
            parts = repo_url.rstrip('/').split('/')
            if 'github.com' not in repo_url or len(parts) < 5:
                logger.error(f"Invalid GitHub URL: {repo_url}")
                return None
                
            username = parts[-2]
            repo = parts[-1]
            
            # Create the model directory
            model_path = os.path.join(self.cache_dir, model_name)
            os.makedirs(model_path, exist_ok=True)
            
            # Use git clone to download the repository
            import subprocess
            result = subprocess.run(
                ["git", "clone", repo_url, model_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Git clone failed: {result.stderr}")
                return None
            
            # Update cached models
            self.cached_models[model_name] = model_path
            
            logger.info(f"Successfully downloaded {repo_url} to {model_path}")
            return model_path
            
        except Exception as e:
            logger.error(f"Error downloading from GitHub: {e}")
            return None
    
    def list_available_models(self, source: str = "huggingface") -> List[Dict[str, Any]]:
        """
        List available models from a source
        
        Args:
            source: Source to list models from ("huggingface" or "cached")
            
        Returns:
            List of model information dictionaries
        """
        if source == "cached":
            # Return locally cached models
            return [
                {"name": name, "path": path, "source": "cache"}
                for name, path in self.cached_models.items()
            ]
        
        elif source == "huggingface":
            # Return a list of recommended models from Hugging Face
            # This is a static list to avoid making API calls
            return [
                {"name": "gpt2", "description": "GPT-2 small model (124M parameters)", "source": "huggingface"},
                {"name": "gpt2-medium", "description": "GPT-2 medium model (355M parameters)", "source": "huggingface"},
                {"name": "distilgpt2", "description": "Distilled version of GPT-2", "source": "huggingface"},
                {"name": "facebook/opt-125m", "description": "OPT small model (125M parameters)", "source": "huggingface"},
                {"name": "EleutherAI/gpt-neo-125M", "description": "GPT-Neo small model", "source": "huggingface"}
            ]
        
        else:
            logger.error(f"Unknown source: {source}")
            return []
    
    def create_model_clone(self, original_model: str, new_model_name: str, 
                         modifications: Dict[str, Any] = None) -> Optional[str]:
        """
        Create a clone of an existing model with optional modifications
        
        Args:
            original_model: Name of the model to clone
            new_model_name: Name for the cloned model
            modifications: Dictionary of modifications to apply
            
        Returns:
            Path to the cloned model or None on failure
        """
        try:
            logger.info(f"Creating clone of {original_model} as {new_model_name}")
            
            # Get path to original model
            original_path = self.get_model_path(original_model)
            
            # Create path for new model
            new_model_path = os.path.join(self.cache_dir, new_model_name)
            
            # Clone the model by copying files
            shutil.copytree(original_path, new_model_path, dirs_exist_ok=True)
            
            # Apply modifications if provided
            if modifications:
                logger.info(f"Applying modifications to cloned model")
                # This would be where model modifications are applied
                # For now, we're just creating a marker file with the modifications
                with open(os.path.join(new_model_path, "modifications.txt"), "w") as f:
                    for key, value in modifications.items():
                        f.write(f"{key}: {value}\n")
            
            # Update cached models
            self.cached_models[new_model_name] = new_model_path
            
            logger.info(f"Successfully cloned model to {new_model_path}")
            return new_model_path
            
        except Exception as e:
            logger.error(f"Error cloning model: {e}")
            return None
