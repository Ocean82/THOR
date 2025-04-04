import os
import logging
import json
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ModelIntegrator:
    """
    Model integrator that manages model information and downloads
    from external sources like GitHub and HuggingFace
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize model integrator with basic model info
        
        Args:
            cache_dir: Directory to cache model info and downloads
        """
        # Create a cache directory
        self.cache_dir = cache_dir or os.path.join(os.getcwd(), "model_info")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Dictionary of available models
        self.available_models = {
            "simple_ai": {
                "name": "Simple AI",
                "version": "1.0",
                "description": "Basic rule-based AI model",
                "capabilities": ["conversation", "text generation", "intent recognition"]
            },
            "advanced_ai": {
                "name": "Advanced AI",
                "version": "1.0",
                "description": "More sophisticated AI with extended capabilities",
                "capabilities": ["conversation", "text generation", "intent recognition", "code generation"]
            }
        }
        
        # Save model info to cache directory
        self._save_model_info()
        
        logger.info(f"Model Integrator initialized with {len(self.available_models)} models")
    
    def _save_model_info(self):
        """Save model information to cache directory"""
        try:
            for model_id, model_info in self.available_models.items():
                model_path = os.path.join(self.cache_dir, f"{model_id}.json")
                with open(model_path, 'w') as f:
                    json.dump(model_info, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving model info: {e}")
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Get information about a model
        
        Args:
            model_name: Name of the model to get info for
            
        Returns:
            Dictionary with model information
        """
        return self.available_models.get(model_name, {
            "name": "Unknown Model",
            "version": "unknown",
            "description": "Model information not available",
            "capabilities": []
        })
        
    def get_model_path(self, model_name: str) -> str:
        """
        Get path to a model (simplified version)
        
        Args:
            model_name: Name of the model
            
        Returns:
            Path to the model info file
        """
        return os.path.join(self.cache_dir, f"{model_name}.json")
    
    def list_available_models(self, source: str = "local") -> List[Dict[str, Any]]:
        """
        List all available models
        
        Args:
            source: Source to list models from (ignored in this simplified version)
            
        Returns:
            List of model information dictionaries
        """
        return [
            {"id": model_id, **model_info} 
            for model_id, model_info in self.available_models.items()
        ]
    
    def download_from_github(self, repo_url: str, model_name: str, 
                          branch: str = "main", token: Optional[str] = None) -> Optional[str]:
        """
        Download a model from GitHub
        
        Args:
            repo_url: URL of the GitHub repository
            model_name: Name to save the model under
            branch: Branch to clone (default is "main")
            token: GitHub access token for private repositories
            
        Returns:
            Path to model info file or None on failure
        """
        try:
            import datetime
            # Import GitHub libraries
            from github import Github, GithubException
            import git
            
            # Create output directory if not exists
            model_dir = os.path.join(self.cache_dir, model_name)
            os.makedirs(model_dir, exist_ok=True)
            
            # Parse the GitHub repository URL
            # Example: https://github.com/username/repository
            if "github.com/" in repo_url:
                repo_parts = repo_url.split("github.com/")[-1].strip("/").split("/")
                if len(repo_parts) >= 2:
                    repo_owner = repo_parts[0]
                    repo_name = repo_parts[1]
                else:
                    raise ValueError(f"Invalid GitHub repository URL: {repo_url}")
            else:
                raise ValueError(f"Not a valid GitHub URL: {repo_url}")
            
            # Initialize GitHub API
            if token:
                g = Github(token)
                logger.info(f"Authenticated to GitHub with provided token")
            else:
                g = Github()  # Anonymous access (rate limited)
                logger.info("Using anonymous GitHub access (rate limited)")
            
            try:
                # Get repository information
                repo = g.get_repo(f"{repo_owner}/{repo_name}")
                logger.info(f"Accessed GitHub repository: {repo.full_name}")
                
                # Get repository metadata
                stars = repo.stargazers_count
                forks = repo.forks_count
                description = repo.description or f"Model downloaded from {repo_url}"
                
                # Try to determine model capabilities from repo topics and description
                topics = repo.get_topics()
                capabilities = list(topics) if topics else ["downloaded", "external", "github"]
                
                # For ML models, add standard capabilities based on topics
                if any(topic in topics for topic in ["ml", "machine-learning", "ai", "model"]):
                    if "nlp" in topics or "text" in topics:
                        capabilities.extend(["text-generation", "nlp"])
                    if "vision" in topics or "image" in topics:
                        capabilities.extend(["image-processing", "vision"])
                
                # Get release version if available
                try:
                    latest_release = repo.get_latest_release()
                    version = latest_release.tag_name
                except GithubException:
                    version = "main"  # No releases found
                
                # Clone the repository using GitPython
                clone_url = repo.clone_url
                if token:
                    # Insert token into clone URL for authentication
                    parsed_url = list(clone_url.partition("github.com"))
                    clone_url = f"{parsed_url[0]}:{token}@github.com{parsed_url[2]}"
                
                # Clone the repository
                logger.info(f"Cloning repository {repo_owner}/{repo_name} to {model_dir}")
                
                # If directory already has contents, remove them
                if os.path.exists(model_dir) and os.listdir(model_dir):
                    import shutil
                    shutil.rmtree(model_dir)
                    os.makedirs(model_dir, exist_ok=True)
                
                git.Repo.clone_from(clone_url, model_dir, branch=branch)
                
                # Create model entry with GitHub information
                self.available_models[model_name] = {
                    "name": model_name,
                    "version": version,
                    "description": description,
                    "source": "github",
                    "repo_url": repo_url,
                    "repo_owner": repo_owner,
                    "repo_name": repo_name,
                    "stars": stars,
                    "forks": forks,
                    "branch": branch,
                    "capabilities": list(set(capabilities)),  # Remove duplicates
                    "download_time": datetime.datetime.now().isoformat(),
                    "local_path": model_dir
                }
                
                # Save model info
                self._save_model_info()
                
                logger.info(f"Successfully downloaded GitHub repository to {model_dir}")
                return self.get_model_path(model_name)
                
            except GithubException as e:
                logger.error(f"GitHub API error: {e}")
                return None
                
        except ImportError as e:
            logger.error(f"Required package not available: {e}")
            logger.error("Please install PyGithub and GitPython packages")
            return None
        except Exception as e:
            logger.error(f"Error downloading from GitHub: {e}")
            return None
    
    def download_from_huggingface(self, model_id: str, model_name: Optional[str] = None, 
                               token: Optional[str] = None) -> Optional[str]:
        """
        Download a model from HuggingFace Hub using HTTP requests
        
        Args:
            model_id: The HuggingFace model ID (e.g. 'gpt2', 'bert-base-uncased')
            model_name: The name to save the model under (defaults to model_id)
            token: HuggingFace access token for private models
            
        Returns:
            Path to model info file or None on failure
        """
        try:
            import datetime
            import requests
            import shutil
            
            # Use model_id as model_name if not provided
            if not model_name:
                model_name = model_id.replace('/', '_')  # Replace slashes for filesystem safety
            
            # Create model directory
            model_dir = os.path.join(self.cache_dir, model_name)
            os.makedirs(model_dir, exist_ok=True)
            
            # If directory already has contents, clean it
            if os.path.exists(model_dir) and os.listdir(model_dir):
                shutil.rmtree(model_dir)
                os.makedirs(model_dir, exist_ok=True)
            
            # Setup API headers
            headers = {"Accept": "application/json"}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
            # Get model information from HuggingFace API
            api_url = f"https://huggingface.co/api/models/{model_id}"
            logger.info(f"Fetching model information from {api_url}")
            
            response = requests.get(api_url, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"Error fetching model information: {response.status_code} - {response.text}")
                return None
            
            model_info = response.json()
            
            # Extract model metadata
            model_metadata = {
                "name": model_info.get("modelId", model_id),
                "version": model_info.get("sha", "latest"),
                "description": model_info.get("description", f"Model downloaded from HuggingFace: {model_id}"),
                "source": "huggingface",
                "model_id": model_id,
                "author": model_info.get("author"),
                "likes": model_info.get("likes"),
                "downloads": model_info.get("downloads"),
                "tags": model_info.get("tags", []),
                "pipeline_tag": model_info.get("pipeline_tag"),
                "siblings": [],  # Will store downloaded files
                "download_time": datetime.datetime.now().isoformat(),
                "local_path": model_dir
            }
            
            # Determine capabilities based on pipeline tag and tags
            capabilities = ["downloaded", "external", "huggingface"]
            
            pipeline_tag = model_info.get("pipeline_tag")
            if pipeline_tag:
                capabilities.append(pipeline_tag)
                
                # Map pipeline tags to capabilities
                pipeline_capability_map = {
                    "text-generation": ["text-generation", "nlp"],
                    "fill-mask": ["fill-mask", "nlp"],
                    "token-classification": ["token-classification", "nlp"],
                    "text-classification": ["text-classification", "nlp"],
                    "question-answering": ["question-answering", "nlp"],
                    "summarization": ["summarization", "nlp"],
                    "translation": ["translation", "nlp"],
                    "image-classification": ["image-classification", "vision"],
                    "object-detection": ["object-detection", "vision"],
                    "image-segmentation": ["image-segmentation", "vision"],
                    "text-to-image": ["text-to-image", "vision"],
                    "text-to-speech": ["text-to-speech", "audio"],
                    "automatic-speech-recognition": ["speech-recognition", "audio"]
                }
                
                if pipeline_tag in pipeline_capability_map:
                    capabilities.extend(pipeline_capability_map[pipeline_tag])
            
            # Add additional capabilities based on tags
            tags = model_info.get("tags", [])
            for tag in tags:
                if tag not in capabilities:
                    capabilities.append(tag)
            
            model_metadata["capabilities"] = list(set(capabilities))  # Remove duplicates
            
            # Download model files
            # First check which files are available
            sibling_api_url = f"https://huggingface.co/api/models/{model_id}/siblings"
            siblings_response = requests.get(sibling_api_url, headers=headers)
            
            if siblings_response.status_code != 200:
                logger.error(f"Error fetching model files: {siblings_response.status_code}")
                # Continue with basic model metadata anyway
            else:
                siblings = siblings_response.json()
                model_metadata["siblings"] = [s.get("rfilename") for s in siblings]
                
                # Download key files (config.json, model.safetensors, tokenizer.json)
                key_files = ["config.json", "model.safetensors", "model.bin", "tokenizer.json", "vocab.json", "README.md"]
                downloaded_files = []
                
                for sibling in siblings:
                    filename = sibling.get("rfilename")
                    
                    # Only download key files to avoid excessive downloads
                    if any(filename.endswith(key_file) for key_file in key_files) or filename in key_files:
                        file_url = f"https://huggingface.co/{model_id}/resolve/main/{filename}"
                        file_path = os.path.join(model_dir, filename)
                        
                        logger.info(f"Downloading {filename}")
                        file_response = requests.get(file_url, headers=headers, stream=True)
                        
                        if file_response.status_code == 200:
                            with open(file_path, 'wb') as f:
                                file_response.raw.decode_content = True
                                shutil.copyfileobj(file_response.raw, f)
                            downloaded_files.append(filename)
                        else:
                            logger.warning(f"Failed to download {filename}: {file_response.status_code}")
                
                model_metadata["downloaded_files"] = downloaded_files
                
                # Download the model card if available
                model_card_url = f"https://huggingface.co/{model_id}/raw/main/README.md"
                model_card_response = requests.get(model_card_url, headers=headers)
                
                if model_card_response.status_code == 200:
                    with open(os.path.join(model_dir, "README.md"), 'wb') as f:
                        f.write(model_card_response.content)
                    model_metadata["has_model_card"] = True
                else:
                    model_metadata["has_model_card"] = False
            
            # Add the model to available models
            self.available_models[model_name] = model_metadata
            self._save_model_info()
            
            logger.info(f"Successfully downloaded HuggingFace model {model_id} to {model_dir}")
            return self.get_model_path(model_name)
        
        except ImportError as e:
            logger.error(f"Required package not available: {e}")
            logger.error("Please install requests package")
            return None
        except Exception as e:
            logger.error(f"Error downloading from HuggingFace: {e}")
            return None
    
    def create_model_clone(self, original_model: str, new_model_name: str, 
                  modifications: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Create a clone of an existing model with modifications
        
        Args:
            original_model: ID of the model to clone
            new_model_name: ID for the cloned model
            modifications: Dictionary of modifications to apply
            
        Returns:
            Path to model info file or None on failure
        """
        try:
            if original_model not in self.available_models:
                logger.error(f"Original model {original_model} not found")
                return None
            
            # Clone the model information
            new_model_info = self.available_models[original_model].copy()
            
            # Apply modifications
            if modifications:
                for key, value in modifications.items():
                    if key in new_model_info:
                        if isinstance(new_model_info[key], list) and isinstance(value, list):
                            # Append to lists
                            new_model_info[key].extend(value)
                        else:
                            # Override other values
                            new_model_info[key] = value
            
            # Update name and version to indicate it's a clone
            if "name" in new_model_info:
                new_model_info["name"] = f"{new_model_info['name']} (Clone)"
            if "version" in new_model_info:
                new_model_info["version"] = f"{new_model_info['version']}-clone"
            
            # Add clone information
            new_model_info["cloned_from"] = original_model
            
            # Add the new model
            self.available_models[new_model_name] = new_model_info
            self._save_model_info()
            
            logger.info(f"Created clone of {original_model} as {new_model_name}")
            return self.get_model_path(new_model_name)
            
        except Exception as e:
            logger.error(f"Error creating model clone: {e}")
            return None
