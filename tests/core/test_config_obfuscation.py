"""
Tests for Code Obfuscation Detection in Config Validator

Tests that dangerous patterns can't be bypassed through obfuscation techniques.
"""

import pytest
from core.config_validator import validate_config


class TestObfuscationBypass:
    """Test detection of obfuscated dangerous code patterns."""
    
    def test_getattr_bypass_detected(self):
        """getattr(__builtins__, 'eval') bypass should be detected."""
        config = {
            "plugins": {
                "my_plugin": {
                    "command": "getattr(__builtins__, 'eval')('code')"
                }
            }
        }
        with pytest.raises(ValueError, match="Dangerous pattern.*getattr"):
            validate_config(config)
    
    def test_globals_access_detected(self):
        """globals()['eval'] bypass should be detected."""
        config = {
            "plugins": {
                "my_plugin": {
                    "script": "globals()['eval']('malicious')"
                }
            }
        }
        with pytest.raises(ValueError, match="Dangerous pattern.*globals"):
            validate_config(config)
    
    def test_locals_access_detected(self):
        """locals() access should be detected."""
        config = {
            "plugins": {
                "my_plugin": {
                    "code": "locals()['__builtins__']"
                }
            }
        }
        with pytest.raises(ValueError, match="Dangerous pattern.*locals"):
            validate_config(config)
    
    def test_builtins_access_detected(self):
        """Direct __builtins__ access should be detected."""
        config = {
            "plugins": {
                "my_plugin": {
                    "exploit": "__builtins__['eval']('code')"
                }
            }
        }
        with pytest.raises(ValueError, match="Dangerous pattern.*__builtins__"):
            validate_config(config)
    
    def test_direct_eval_still_detected(self):
        """Direct eval() should still be detected."""
        config = {
            "plugins": {
                "my_plugin": {
                    "command": "eval('code')"
                }
            }
        }
        with pytest.raises(ValueError, match="Dangerous pattern.*eval"):
            validate_config(config)
    
    def test_direct_exec_still_detected(self):
        """Direct exec() should still be detected."""
        config = {
            "plugins": {
                "my_plugin": {
                    "command": "exec('code')"
                }
            }
        }
        with pytest.raises(ValueError, match="Dangerous pattern.*exec"):
            validate_config(config)
    
    def test_compile_detected(self):
        """compile() function should be detected."""
        config = {
            "plugins": {
                "my_plugin": {
                    "code": "compile('code', '<string>', 'exec')"
                }
            }
        }
        with pytest.raises(ValueError, match="Dangerous pattern.*compile"):
            validate_config(config)
    
    def test_open_detected(self):
        """open() function should be detected."""
        config = {
            "plugins": {
                "my_plugin": {
                    "file_op": "open('/etc/passwd').read()"
                }
            }
        }
        with pytest.raises(ValueError, match="Dangerous pattern.*(open|/etc/)"):
            validate_config(config)
    
    def test_import_detected(self):
        """__import__ should be detected."""
        config = {
            "plugins": {
                "my_plugin": {
                    "import_hack": "__import__('os').system('ls')"
                }
            }
        }
        with pytest.raises(ValueError, match="Dangerous pattern.*__import__"):
            validate_config(config)


class TestCaseInsensitivity:
    """Test that detection is case-insensitive."""
    
    def test_eval_uppercase_detected(self):
        """EVAL() should be detected (case insensitive)."""
        config = {
            "plugins": {
                "my_plugin": {
                    "command": "EVAL('code')"
                }
            }
        }
        with pytest.raises(ValueError, match="Dangerous pattern"):
            validate_config(config)
    
    def test_exec_mixed_case_detected(self):
        """ExEc() should be detected (case insensitive)."""
        config = {
            "plugins": {
                "my_plugin": {
                    "command": "ExEc('code')"
                }
            }
        }
        with pytest.raises(ValueError, match="Dangerous pattern"):
            validate_config(config)
    
    def test_getattr_uppercase_detected(self):
        """GETATTR() should be detected (case insensitive)."""
        config = {
            "plugins": {
                "my_plugin": {
                    "code": "GETATTR(obj, 'eval')"
                }
            }
        }
        with pytest.raises(ValueError, match="Dangerous pattern"):
            validate_config(config)


class TestNestedObfuscation:
    """Test obfuscation in nested configs."""
    
    def test_nested_getattr_detected(self):
        """Nested getattr should be detected."""
        config = {
            "plugins": {
                "my_plugin": {
                    "settings": {
                        "advanced": {
                            "code": "getattr(__builtins__, 'eval')"
                        }
                    }
                }
            }
        }
        with pytest.raises(ValueError, match="Dangerous pattern.*getattr"):
            validate_config(config)
    
    def test_nested_globals_detected(self):
        """Nested globals() should be detected."""
        config = {
            "plugins": {
                "my_plugin": {
                    "database": {
                        "init_script": "globals()['eval']('code')"
                    }
                }
            }
        }
        with pytest.raises(ValueError, match="Dangerous pattern.*globals"):
            validate_config(config)


class TestSafePatterns:
    """Test that legitimate patterns are not flagged."""
    
    def test_evaluation_word_safe(self):
        """Word 'evaluation' should be safe (not 'eval(')."""
        config = {
            "plugins": {
                "my_plugin": {
                    "description": "This is for evaluation purposes"
                }
            }
        }
        # Should not raise
        validate_config(config)
    
    def test_execute_word_safe(self):
        """Word 'execute' should be safe (not 'exec(')."""
        config = {
            "plugins": {
                "my_plugin": {
                    "action": "execute the plan"
                }
            }
        }
        # Should not raise
        validate_config(config)
    
    def test_compiled_word_safe(self):
        """Word 'compiled' should be safe (not 'compile(')."""
        config = {
            "plugins": {
                "my_plugin": {
                "note": "This uses compiled regex patterns"
                }
            }
        }
        # Should not raise
        validate_config(config)
