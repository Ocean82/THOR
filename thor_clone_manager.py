import json
import os
import logging
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.exc import SQLAlchemyError

from app import db

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Import ThorClone from models
from models import ThorClone


class ThorCloneManager:
    """
    Manages THOR clone creation, activation, and versioning
    """
    
    def __init__(self, models_dir="thor_models"):
        """
        Initialize the THOR clone manager
        
        Args:
            models_dir: Directory to store model information
        """
        self.models_dir = models_dir
        
        # Create models directory if it doesn't exist
        if not os.path.exists(models_dir):
            os.makedirs(models_dir)
            logger.info(f"Created models directory: {models_dir}")
    
    def list_clones(self) -> List[Dict[str, Any]]:
        """
        List all available THOR clones
        
        Returns:
            List of clone information dictionaries
        """
        try:
            clones = db.session.query(ThorClone).all()
            result = []
            
            for clone in clones:
                clone_info = {
                    "id": clone.id,
                    "name": clone.clone_name,
                    "base_version": clone.base_version,
                    "description": clone.description,
                    "created_at": clone.created_at.isoformat(),
                    "modified_at": clone.modified_at.isoformat(),
                    "is_active": clone.is_active,
                    "capabilities": json.loads(clone.capabilities) if clone.capabilities else {}
                }
                result.append(clone_info)
            
            return result
        except SQLAlchemyError as e:
            logger.error(f"Database error when listing clones: {e}")
            return []
    
    def create_clone(self, base_version: str, description: str, capabilities: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new THOR clone
        
        Args:
            base_version: Base version to clone from
            description: Description of the clone
            capabilities: Dictionary of capabilities
            
        Returns:
            Dictionary with clone information or None on failure
        """
        try:
            # Get the next clone number
            next_num = self._get_next_clone_number()
            clone_name = f"THOR{next_num}"
            
            # Create the clone entry
            new_clone = ThorClone(
                clone_name=clone_name,
                base_version=base_version,
                description=description,
                capabilities=json.dumps(capabilities),
                is_active=False
            )
            
            # Save clone information to file
            model_path = os.path.join(self.models_dir, f"{clone_name}.json")
            with open(model_path, 'w') as f:
                json.dump({
                    "name": clone_name,
                    "base_version": base_version,
                    "description": description,
                    "created_at": datetime.utcnow().isoformat(),
                    "capabilities": capabilities
                }, f, indent=2)
            
            # Add to database
            db.session.add(new_clone)
            db.session.commit()
            
            logger.info(f"Created new clone: {clone_name}")
            
            return {
                "id": new_clone.id,
                "name": new_clone.clone_name,
                "base_version": new_clone.base_version,
                "description": new_clone.description,
                "created_at": new_clone.created_at.isoformat(),
                "is_active": new_clone.is_active,
                "capabilities": capabilities
            }
        except Exception as e:
            logger.error(f"Clone creation error: {e}")
            db.session.rollback()
            return None
    
    def activate_clone(self, clone_name: str) -> bool:
        """
        Activate a specific THOR clone
        
        Args:
            clone_name: Name of the clone to activate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Deactivate all clones
            db.session.query(ThorClone).update({"is_active": False})
            
            # Activate the specified clone
            clone = db.session.query(ThorClone).filter_by(clone_name=clone_name).first()
            if clone:
                clone.is_active = True
                db.session.commit()
                logger.info(f"Activated clone: {clone_name}")
                return True
            else:
                logger.error(f"Clone not found: {clone_name}")
                return False
        except SQLAlchemyError as e:
            logger.error(f"Database error when activating clone: {e}")
            db.session.rollback()
            return False
    
    def deactivate_all_clones(self) -> bool:
        """
        Deactivate all THOR clones
        
        Returns:
            True if successful, False otherwise
        """
        try:
            db.session.query(ThorClone).update({"is_active": False})
            db.session.commit()
            logger.info("Deactivated all clones")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database error when deactivating clones: {e}")
            db.session.rollback()
            return False
    
    def get_active_clone(self) -> Optional[Dict[str, Any]]:
        """
        Get the currently active THOR clone
        
        Returns:
            Dictionary with clone information or None if no active clone
        """
        try:
            clone = db.session.query(ThorClone).filter_by(is_active=True).first()
            if clone:
                return {
                    "id": clone.id,
                    "name": clone.clone_name,
                    "base_version": clone.base_version,
                    "description": clone.description,
                    "created_at": clone.created_at.isoformat(),
                    "modified_at": clone.modified_at.isoformat(),
                    "capabilities": json.loads(clone.capabilities) if clone.capabilities else {}
                }
            return None
        except SQLAlchemyError as e:
            logger.error(f"Database error when getting active clone: {e}")
            return None
    
    def update_clone(self, clone_name: str, updates: Dict[str, Any]) -> bool:
        """
        Update a THOR clone with new capabilities or description
        
        Args:
            clone_name: Name of the clone to update
            updates: Dictionary of updates to apply
            
        Returns:
            True if successful, False otherwise
        """
        try:
            clone = db.session.query(ThorClone).filter_by(clone_name=clone_name).first()
            if not clone:
                logger.error(f"Clone not found: {clone_name}")
                return False
            
            # Update fields based on the updates dictionary
            if "description" in updates:
                clone.description = updates["description"]
            
            if "capabilities" in updates:
                # Merge with existing capabilities
                current_capabilities = json.loads(clone.capabilities) if clone.capabilities else {}
                current_capabilities.update(updates["capabilities"])
                clone.capabilities = json.dumps(current_capabilities)
            
            # Update the model file
            model_path = os.path.join(self.models_dir, f"{clone_name}.json")
            if os.path.exists(model_path):
                with open(model_path, 'r') as f:
                    model_data = json.load(f)
                
                # Update the model data
                if "description" in updates:
                    model_data["description"] = updates["description"]
                
                if "capabilities" in updates:
                    if "capabilities" not in model_data:
                        model_data["capabilities"] = {}
                    model_data["capabilities"].update(updates["capabilities"])
                
                # Save updated model file
                with open(model_path, 'w') as f:
                    json.dump(model_data, f, indent=2)
            
            db.session.commit()
            logger.info(f"Updated clone: {clone_name}")
            return True
        except Exception as e:
            logger.error(f"Error updating clone: {e}")
            db.session.rollback()
            return False
    
    def _get_next_clone_number(self) -> int:
        """
        Get the next clone number
        
        Returns:
            Next clone number as integer
        """
        try:
            # Get the highest clone number
            highest_clone = db.session.query(ThorClone).order_by(ThorClone.id.desc()).first()
            if highest_clone:
                # Extract number from clone name (e.g., "THOR1" -> 1)
                current_num = int(highest_clone.clone_name.replace("THOR", ""))
                return current_num + 1
            else:
                return 1
        except Exception:
            # If there's an error, start with 1
            return 1
    
    def delete_clone(self, clone_name: str) -> bool:
        """
        Delete a THOR clone
        
        Args:
            clone_name: Name of the clone to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            clone = db.session.query(ThorClone).filter_by(clone_name=clone_name).first()
            if not clone:
                logger.error(f"Clone not found: {clone_name}")
                return False
            
            # Delete the model file
            model_path = os.path.join(self.models_dir, f"{clone_name}.json")
            if os.path.exists(model_path):
                os.remove(model_path)
            
            # Delete from database
            db.session.delete(clone)
            db.session.commit()
            
            logger.info(f"Deleted clone: {clone_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting clone: {e}")
            db.session.rollback()
            return False