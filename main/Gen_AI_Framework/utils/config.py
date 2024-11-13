import json
import os
from pathlib import Path

class Config:
    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._load_config()
        return cls._instance

    @classmethod
    def _load_config(cls):
        config_path = Path("config/config.json")
        if config_path.exists():
            with open(config_path) as f:
                cls._config = json.load(f)
        else:
            cls._config = {
                "theme": "light",
                "logging_level": "INFO",
                "max_threads": 4,
                "default_tool": "code_review"
            }
            # Create config directory if it doesn't exist
            config_path.parent.mkdir(exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(cls._config, f, indent=4)

    def get(self, key, default=None):
        return self._config.get(key, default)

    def set(self, key, value):
        self._config[key] = value
        self._save_config()

    def _save_config(self):
        with open("config/config.json", 'w') as f:
            json.dump(self._config, f, indent=4)