"""
Tests for Config Validator (Phase 0.2)

Tests security validation of configuration files using validate_config() function.
"""

import pytest
from core.config_validator import validate_config


class TestAPIKeyValidation:
    """Test API key format validation."""
    
    def test_valid_env_var_format(self):
        """Valid API keys in ${ENV_VAR} format should pass."""
        config = {
            "llm": {
                "api_key": "${OPENAI_API_KEY}",
                "model": "gpt-4"
            }
        }
        # Should not raise
        validate_config(config)
    
    def test_hardcoded_api_key_rejected(self):
        """Hardcoded API keys should be rejected."""
        config = {
            "llm": {
                "model": "gpt-4",
                "api_key": "sk-1234567890abcdef"
            }
        }
        with pytest.raises(ValueError, match="api_key must be an environment variable"):
            validate_config(config)
    
    def test_plain_string_api_key_rejected(self):
        """Plain string API keys should be rejected."""
        config = {
            "llm": {
                "model": "gpt-4",
                "api_key": "my_secret_key"
            }
        }
        with pytest.raises(ValueError, match="api_key must be an environment variable"):
            validate_config(config)
    
    def test_missing_llm_config_allowed(self):
        """Missing LLM config should be allowed (optional)."""
        config = {
            "plugins": {}
        }
        # Should not raise
        validate_config(config)


class TestPluginNameValidation:
    """Test plugin name validation."""
    
    def test_valid_plugin_names(self):
        """Valid plugin names should pass."""
        config = {
            "plugins": {
                "my_plugin": {"enabled": True},
                "cognitive_planner": {"enabled": True},
                "tool_bash": {"enabled": True}
            }
        }
        # Should not raise
        validate_config(config)
    
    def test_plugin_with_dash_rejected(self):
        """Plugin names with dashes should be rejected."""
        config = {
            "plugins": {
                "my-plugin": {"enabled": True}
            }
        }
        with pytest.raises(ValueError, match="Invalid plugin name"):
            validate_config(config)
    
    def test_plugin_with_special_chars_rejected(self):
        """Plugin names with special characters should be rejected."""
        config = {
            "plugins": {
                "plugin@hack": {"enabled": True}
            }
        }
        with pytest.raises(ValueError, match="Invalid plugin name"):
            validate_config(config)


class TestDangerousPatternDetection:
    """Test detection of dangerous patterns in config values."""
    
    def test_eval_pattern_rejected(self):
        """Config values with 'eval' should be rejected."""
        config = {
            "plugins": {
                "my_plugin": {
                    "command": "eval('malicious code')"
                }
            }
        }
        with pytest.raises(ValueError, match="Dangerous pattern"):
            validate_config(config)
    
    def test_exec_pattern_rejected(self):
        """Config values with 'exec' should be rejected."""
        config = {
            "plugins": {
                "my_plugin": {
                    "script": "exec(open('hack.py').read())"
                }
            }
        }
        with pytest.raises(ValueError, match="Dangerous pattern"):
            validate_config(config)
    
    def test_path_traversal_rejected(self):
        """Config values with '../' should be rejected."""
        config = {
            "plugins": {
                "file_reader": {
                    "path": "../../etc/passwd"
                }
            }
        }
        with pytest.raises(ValueError, match="Dangerous pattern"):
            validate_config(config)


class TestConvenienceFunction:
    """Test the validate_config() convenience function."""
    
    def test_valid_config_passes(self):
        """Valid config should pass without raising."""
        config = {
            "llm": {
                "api_key": "${OPENAI_API_KEY}",
                "model": "gpt-4"
            },
            "plugins": {
                "cognitive_planner": {"enabled": True}
            }
        }
        # Should not raise
        validate_config(config)
    
    def test_invalid_config_raises(self):
        """Invalid config should raise ValueError."""
        config = {
            "llm": {
                "api_key": "hardcoded_key"
            }
        }
        with pytest.raises(ValueError):
            validate_config(config)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_config(self):
        """Empty config should be valid."""
        config = {}
        # Should not raise
        validate_config(config)
    
    def test_none_values_handled(self):
        """None values should be handled gracefully."""
        config = {
            "plugins": {
                "my_plugin": None
            }
        }
        # Should not raise
        validate_config(config)
    
    def test_numeric_values_safe(self):
        """Numeric values should be safe."""
        config = {
            "settings": {
                "timeout": 30,
                "max_retries": 3,
                "threshold": 0.95
            }
        }
        # Should not raise
        validate_config(config)
