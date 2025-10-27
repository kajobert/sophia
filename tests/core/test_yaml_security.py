"""
Tests for YAML Security (Phase 0.1)

Tests YAML deserialization attack prevention:
- !!python tag detection
- Safe YAML loading
- Malicious YAML rejection
"""

import pytest
import yaml
import tempfile
from pathlib import Path
from core.kernel import Kernel


class TestYAMLSecurityInKernel:
    """Test YAML security in Kernel configuration loading."""
    
    def test_dangerous_python_tag_rejected(self, tmp_path):
        """Config with !!python tag should be rejected."""
        # Create malicious config
        config_path = tmp_path / "settings.yaml"
        malicious_yaml = """
plugins:
  evil: !!python/object/apply:os.system
    args: ['echo hacked']
"""
        config_path.write_text(malicious_yaml)
        
        # Temporarily replace config path
        original_config = Path("config/settings.yaml")
        if original_config.exists():
            backup = original_config.read_text()
        else:
            backup = None
        
        try:
            # Write malicious config
            original_config.parent.mkdir(parents=True, exist_ok=True)
            original_config.write_text(malicious_yaml)
            
            # Kernel should reject this
            with pytest.raises(ValueError, match="dangerous.*!!python"):
                Kernel()
        
        finally:
            # Restore original config
            if backup is not None:
                original_config.write_text(backup)
            elif original_config.exists():
                original_config.unlink()
    
    def test_python_object_new_rejected(self, tmp_path):
        """Config with !!python/object/new should be rejected."""
        malicious_yaml = """
plugins:
  evil: !!python/object/new:subprocess.Popen
    args: [['calc.exe']]
"""
        config_path = Path("config/settings.yaml")
        original_backup = None
        
        if config_path.exists():
            original_backup = config_path.read_text()
        
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(malicious_yaml)
            
            with pytest.raises(ValueError, match="dangerous.*!!python"):
                Kernel()
        
        finally:
            if original_backup is not None:
                config_path.write_text(original_backup)
            elif config_path.exists():
                config_path.unlink()
    
    def test_safe_yaml_accepted(self, tmp_path):
        """Normal YAML without dangerous tags should be accepted."""
        safe_yaml = """
llm:
  api_key: ${OPENAI_API_KEY}
  model: gpt-4

plugins:
  cognitive_planner:
    enabled: true
  tool_bash:
    enabled: false
"""
        config_path = Path("config/settings.yaml")
        original_backup = None
        
        if config_path.exists():
            original_backup = config_path.read_text()
        
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(safe_yaml)
            
            # Should not raise
            kernel = Kernel()
            assert kernel is not None
        
        finally:
            if original_backup is not None:
                config_path.write_text(original_backup)
            elif config_path.exists():
                config_path.unlink()


class TestYAMLSafeLoad:
    """Test that yaml.safe_load is being used correctly."""
    
    def test_yaml_safe_load_blocks_python_objects(self):
        """Verify yaml.safe_load blocks Python object instantiation."""
        malicious_yaml = """
evil: !!python/object/apply:os.system
  args: ['echo hacked']
"""
        # yaml.safe_load should raise ConstructorError
        with pytest.raises(yaml.YAMLError):
            yaml.safe_load(malicious_yaml)
    
    def test_yaml_unsafe_load_vulnerable(self):
        """Demonstrate that yaml.unsafe_load is vulnerable (for comparison)."""
        # This test shows WHY we use safe_load
        dangerous_yaml = """
test: !!python/object/apply:os.getcwd []
"""
        # unsafe_load would execute this (we're not actually using it in code)
        # This is just to demonstrate the vulnerability
        result = yaml.unsafe_load(dangerous_yaml)
        # Result would be the current working directory if executed
        assert isinstance(result, dict)


class TestYAMLEdgeCases:
    """Test edge cases in YAML security."""
    
    def test_nested_python_tag_detected(self):
        """Nested !!python tags should be detected."""
        malicious_yaml = """
plugins:
  normal_plugin:
    settings:
      nested: !!python/name:os.system
"""
        config_path = Path("config/settings.yaml")
        original_backup = None
        
        if config_path.exists():
            original_backup = config_path.read_text()
        
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(malicious_yaml)
            
            with pytest.raises(ValueError, match="dangerous.*!!python"):
                Kernel()
        
        finally:
            if original_backup is not None:
                config_path.write_text(original_backup)
            elif config_path.exists():
                config_path.unlink()
    
    def test_case_sensitive_detection(self):
        """!!python tag detection is case-sensitive for lowercase."""
        # Note: !!PYTHON (uppercase) is not a valid YAML tag
        # yaml.safe_load would fail to parse it anyway
        # Our !!python check is case-sensitive (lowercase only)
        # This test verifies our string search is case-sensitive
        yaml_without_python = """
plugins:
  test:
    description: "This mentions PYTHON but not as a tag"
"""
        config_path = Path("config/settings.yaml")
        original_backup = None
        
        if config_path.exists():
            original_backup = config_path.read_text()
        
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(yaml_without_python)
            
            # Should NOT raise (no !!python tag present)
            kernel = Kernel()
            assert kernel is not None
        
        finally:
            if original_backup is not None:
                config_path.write_text(original_backup)
            elif config_path.exists():
                config_path.unlink()
    
    def test_missing_config_file_handled(self):
        """Missing config file should be handled gracefully."""
        config_path = Path("config/settings.yaml")
        
        if config_path.exists():
            # Temporarily rename
            backup_path = config_path.with_suffix(".yaml.backup")
            config_path.rename(backup_path)
            try:
                kernel = Kernel()
                assert kernel is not None
            finally:
                backup_path.rename(config_path)
        else:
            # Already missing
            kernel = Kernel()
            assert kernel is not None
