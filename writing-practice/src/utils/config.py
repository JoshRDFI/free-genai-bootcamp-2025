"""
Configuration management module.
"""
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from .logging import get_logger

logger = get_logger(__name__)

class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize the configuration manager.
        
        Args:
            base_dir: Base directory for the application
        """
        self.base_dir = base_dir or Path(__file__).parent.parent.parent
        self.config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from files."""
        try:
            # Load default config
            config_path = self.base_dir / "config" / "default_config.json"
            if config_path.exists():
                with open(config_path) as f:
                    self.config.update(json.load(f))
            
            # Load prompts
            prompts_path = self.base_dir / "config" / "prompts.yaml"
            if prompts_path.exists():
                with open(prompts_path) as f:
                    self.config['prompts'] = yaml.safe_load(f)
            
            # Set up paths
            self.config.update({
                'data_dir': self.base_dir / "data",
                'temp_dir': self.base_dir / "data" / "temp",
                'db_path': self.base_dir / "data" / "db" / "app.db",
                'sentences_path': self.base_dir / "data" / "sentences" / "sentences.json"
            })
            
            # Create necessary directories
            for path in [self.config['data_dir'], 
                        self.config['temp_dir'],
                        self.config['db_path'].parent,
                        self.config['sentences_path'].parent]:
                path.mkdir(parents=True, exist_ok=True)
            
            logger.info("Configuration loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            # Set default values
            self.config = {
                'data_dir': self.base_dir / "data",
                'temp_dir': self.base_dir / "data" / "temp",
                'db_path': self.base_dir / "data" / "db" / "app.db",
                'sentences_path': self.base_dir / "data" / "sentences" / "sentences.json",
                'prompts': {}
            }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)
    
    def update(self, key: str, value: Any) -> None:
        """
        Update a configuration value.
        
        Args:
            key: Configuration key
            value: New value
        """
        self.config[key] = value
    
    def save(self) -> None:
        """Save configuration to files."""
        try:
            # Save default config
            config_path = self.base_dir / "config" / "default_config.json"
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            # Save prompts
            prompts_path = self.base_dir / "config" / "prompts.yaml"
            with open(prompts_path, 'w') as f:
                yaml.dump(self.config.get('prompts', {}), f)
            
            logger.info("Configuration saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

# Create singleton instance
_config_manager = None

def get_config() -> Dict[str, Any]:
    """Get the configuration dictionary."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager.config 