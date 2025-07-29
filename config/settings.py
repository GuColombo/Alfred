import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from loguru import logger

class ConfigManager:
    """Manages Alfred's configuration settings."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.config_dir = self.project_root / "config"
        self.config_file = self.config_dir / "alfred_config.json"
        self.env_file = self.project_root / ".env"
        
        # Load environment variables
        load_dotenv(self.env_file)
        
        # Load or create configuration
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_file}")
                return config
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}, using defaults")
        
        # Default configuration
        default_config = {
            "memory": {
                "persist_path": str(self.project_root / "data" / "memory"),
                "vector_store": "chromadb",
                "max_memory_size": 1000000,  # 1M entries
                "cleanup_interval": 86400    # 24 hours
            },
            "llm": {
                "default_model": "auto",
                "model_preferences": {
                    "reasoning": "claude",
                    "coding": "gpt4", 
                    "creative": "gemini"
                },
                "max_tokens": 4000,
                "temperature": 0.1
            },
            "plugins": {
                "enabled": True,
                "sandbox_timeout": 300,  # 5 minutes
                "allowed_domains": ["localhost"],
                "plugin_dir": str(self.project_root / "tools" / "plugins")
            },
            "storage": {
                "provider": "onedrive",
                "sync_interval": 3600,  # 1 hour
                "backup_enabled": True,
                "max_file_size": 100000000  # 100MB
            },
            "api": {
                "host": "localhost",
                "port": 8000,
                "enable_cors": True,
                "rate_limit": "100/hour"
            },
            "logging": {
                "level": "INFO",
                "file_path": str(self.project_root / "logs" / "alfred.log"),
                "max_file_size": "10MB",
                "backup_count": 5
            }
        }
        
        # Save default configuration
        self._save_config(default_config)
        return default_config
    
    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to file."""
        self.config_dir.mkdir(exist_ok=True)
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Saved configuration to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation key."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value by dot notation key."""
        keys = key.split('.')
        config = self._config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the final value
        config[keys[-1]] = value
        self._save_config(self._config)
    
    def get_env(self, key: str, default: str = None) -> Optional[str]:
        """Get environment variable."""
        return os.getenv(key, default)
    
    def get_api_keys(self) -> Dict[str, str]:
        """Get all API keys from environment."""
        return {
            "openai": self.get_env("OPENAI_API_KEY"),
            "claude": self.get_env("CLAUDE_API_KEY"), 
            "gemini": self.get_env("GEMINI_API_KEY")
        }
    
    def get_storage_config(self) -> Dict[str, str]:
        """Get OneDrive/Microsoft Graph configuration."""
        return {
            "client_id": self.get_env("MS_CLIENT_ID"),
            "client_secret": self.get_env("MS_CLIENT_SECRET"),
            "tenant_id": self.get_env("MS_TENANT_ID"),
            "redirect_uri": self.get_env("MS_REDIRECT_URI")
        }
    
    def reset(self):
        """Reset configuration to defaults."""
        if self.config_file.exists():
            self.config_file.unlink()
        self._config = self._load_config()
    
    def items(self):
        """Get all configuration items."""
        return self._flatten_dict(self._config).items()
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """Flatten nested dictionary."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

# Global configuration instance
_config_manager = None

def load_config() -> ConfigManager:
    """Load or get cached configuration manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager