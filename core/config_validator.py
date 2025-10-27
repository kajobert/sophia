"""
Configuration Schema Validator

SECURITY: Validates settings.yaml structure and content to prevent:
- Invalid API key formats
- Missing required fields
- Type mismatches
- Injection attacks via config values

Created: 2025-10-27
Purpose: Phase 0 Security - Config Schema Validation
"""

import re
from typing import Dict, Optional, Any
from pathlib import Path


class ConfigValidator:
    """
    Validates configuration dictionary against expected schema.
    
    SECURITY: This prevents configuration-based attacks by:
    1. Validating API key formats (must be env vars ${VAR})
    2. Checking for dangerous values (code injection patterns)
    3. Ensuring required fields are present
    4. Type checking critical values
    """
    
    # SECURITY: API keys MUST be environment variables (not hardcoded)
    ENV_VAR_PATTERN = re.compile(r'^\$\{[A-Z_][A-Z0-9_]*\}$')
    
    # SECURITY: Dangerous patterns that shouldn't appear in config
    DANGEROUS_PATTERNS = [
        r'__import__',
        r'eval\s*\(',
        r'exec\s*\(',
        r'compile\s*\(',
        r'open\s*\(',
        r'\.\./',  # Path traversal
        r'/etc/',  # System paths
        r'/root/',
    ]
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate configuration dictionary.
        
        Args:
            config: Configuration dictionary from YAML
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # 1. Validate LLM section
        if "llm" in config:
            is_valid, error = cls._validate_llm_config(config["llm"])
            if not is_valid:
                return False, f"LLM config error: {error}"
        
        # 2. Validate plugins section
        if "plugins" in config:
            is_valid, error = cls._validate_plugins_config(config["plugins"])
            if not is_valid:
                return False, f"Plugins config error: {error}"
        
        # 3. Scan for dangerous patterns in all string values
        is_valid, error = cls._scan_for_dangerous_patterns(config)
        if not is_valid:
            return False, f"Security violation: {error}"
        
        return True, ""
    
    @classmethod
    def _validate_llm_config(cls, llm_config: Dict[str, Any]) -> tuple[bool, str]:
        """Validate LLM configuration section."""
        
        # Required fields
        if "model" not in llm_config:
            return False, "Missing required field 'model'"
        
        if "api_key" not in llm_config:
            return False, "Missing required field 'api_key'"
        
        # SECURITY: API key must be environment variable
        api_key = llm_config["api_key"]
        if not isinstance(api_key, str):
            return False, "api_key must be a string"
        
        if not cls.ENV_VAR_PATTERN.match(api_key):
            return False, (
                f"api_key must be an environment variable in format ${{VAR_NAME}}, "
                f"got: {api_key[:20]}..."
            )
        
        # Model name should be reasonable
        model = llm_config["model"]
        if not isinstance(model, str) or len(model) > 200:
            return False, "model name is invalid or too long"
        
        return True, ""
    
    @classmethod
    def _validate_plugins_config(cls, plugins_config: Dict[str, Any]) -> tuple[bool, str]:
        """Validate plugins configuration section."""
        
        if not isinstance(plugins_config, dict):
            return False, "plugins must be a dictionary"
        
        # Check each plugin config
        for plugin_name, plugin_conf in plugins_config.items():
            # Plugin name should be safe
            if not re.match(r'^[a-z_][a-z0-9_]*$', plugin_name):
                return False, f"Invalid plugin name: {plugin_name}"
            
            # Plugin config should be dict
            if plugin_conf is not None and not isinstance(plugin_conf, dict):
                return False, f"Plugin '{plugin_name}' config must be a dictionary"
            
            # Check for API keys in plugin configs
            if plugin_conf and isinstance(plugin_conf, dict):
                for key, value in plugin_conf.items():
                    if "api_key" in key.lower() or "key" in key.lower():
                        if isinstance(value, str) and not cls.ENV_VAR_PATTERN.match(value):
                            return False, (
                                f"Plugin '{plugin_name}' has hardcoded API key in '{key}'. "
                                f"Use environment variable: ${{VAR_NAME}}"
                            )
        
        return True, ""
    
    @classmethod
    def _scan_for_dangerous_patterns(cls, config: Any, path: str = "root") -> tuple[bool, str]:
        """
        Recursively scan configuration for dangerous patterns.
        
        SECURITY: Detects potential code injection attempts.
        """
        if isinstance(config, dict):
            for key, value in config.items():
                is_valid, error = cls._scan_for_dangerous_patterns(value, f"{path}.{key}")
                if not is_valid:
                    return False, error
        
        elif isinstance(config, list):
            for i, item in enumerate(config):
                is_valid, error = cls._scan_for_dangerous_patterns(item, f"{path}[{i}]")
                if not is_valid:
                    return False, error
        
        elif isinstance(config, str):
            # Check for dangerous patterns
            for pattern in cls.DANGEROUS_PATTERNS:
                if re.search(pattern, config, re.IGNORECASE):
                    return False, f"Dangerous pattern '{pattern}' found at {path}: {config[:50]}"
        
        return True, ""
    
    @classmethod
    def validate_file(cls, config_path: Path) -> tuple[bool, str]:
        """
        Validate configuration file.
        
        Args:
            config_path: Path to settings.yaml
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        import yaml
        
        if not config_path.exists():
            return False, f"Config file not found: {config_path}"
        
        try:
            with open(config_path, "r") as f:
                raw_content = f.read()
                
                # SECURITY: Check for !!python tags
                if "!!python" in raw_content:
                    return False, "Dangerous !!python tag detected"
                
                # Parse YAML
                config = yaml.safe_load(raw_content)
                
                # Validate schema
                return cls.validate_config(config or {})
        
        except yaml.YAMLError as e:
            return False, f"YAML parsing error: {e}"
        except Exception as e:
            return False, f"Validation error: {e}"


# Convenience function for use in Kernel
def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration and raise exception if invalid.
    
    Args:
        config: Configuration dictionary
        
    Raises:
        ValueError: If configuration is invalid
    """
    is_valid, error = ConfigValidator.validate_config(config)
    if not is_valid:
        raise ValueError(f"Configuration validation failed: {error}")
