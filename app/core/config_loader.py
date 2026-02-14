"""
Configuration Loader
Singleton pattern to load and cache YAML configuration
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigLoader:
    """Singleton configuration loader"""

    _instance: Optional['ConfigLoader'] = None
    _config: Optional[Dict[str, Any]] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self, config_path: str = None) -> Dict[str, Any]:
        """
        Load configuration from YAML file

        Args:
            config_path: Path to config.yaml (default: auto-detect from project root)

        Returns:
            Configuration dictionary
        """
        if self._config is None:
            if config_path is None:
                # Auto-detect: go up from backend/app/core to backend root
                current_dir = Path(__file__).parent
                backend_root = current_dir.parent.parent
                config_path = backend_root / "config.yaml"

            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)

        return self._config

    def reload(self, config_path: str = None):
        """Force reload configuration"""
        self._config = None
        return self.load(config_path)

    def get_celestial_bodies(self) -> Dict[str, list]:
        """Get all celestial bodies configuration"""
        config = self.load()
        return config.get("celestial_bodies", {})

    def get_aspects(self) -> Dict[str, dict]:
        """Get all aspect definitions (major + minor)"""
        config = self.load()
        aspects_config = config.get("aspects", {})
        return {
            **aspects_config.get("major", {}),
            **aspects_config.get("minor", {})
        }

    def get_orb_multipliers(self) -> Dict[str, float]:
        """Get orb multipliers for planets"""
        config = self.load()
        return config.get("aspects", {}).get("orb_multipliers", {})

    def get_house_system_default(self) -> str:
        """Get default house system"""
        config = self.load()
        return config.get("house_systems", {}).get("default", "Placidus")

    def get_house_systems(self) -> Dict[str, dict]:
        """Get available house systems with metadata"""
        config = self.load()
        return config.get("house_systems", {}).get("available", {})

    def get_house_system_codes(self) -> Dict[str, str]:
        """Get house system codes only (name: code mapping)"""
        systems = self.get_house_systems()
        return {name: data.get("code", "P") if isinstance(data, dict) else data
                for name, data in systems.items()}

    def get_calculation_settings(self) -> Dict[str, Any]:
        """Get calculation settings"""
        config = self.load()
        return config.get("calculation", {})

    def get_zodiac_signs(self) -> list:
        """Get zodiac sign definitions"""
        config = self.load()
        return config.get("zodiac", {}).get("signs", [])

    def get_patterns(self) -> Dict[str, dict]:
        """Get aspect pattern definitions"""
        config = self.load()
        return config.get("patterns", {})

    def get_fixed_stars(self) -> Dict[str, Any]:
        """Get fixed stars configuration"""
        config = self.load()
        celestial = config.get("celestial_bodies", {})
        return celestial.get("fixed_stars", {})


# Singleton instance
config_loader = ConfigLoader()
