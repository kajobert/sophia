import pytest
from core.utils import CustomJSONEncoder
import json


class Dummy:
    def __init__(self, x):
        self.x = x

    def __str__(self):
        return f"Dummy({self.x})"


def test_custom_json_encoder_handles_object():
    d = Dummy(42)
    # Should raise a TypeError for non-serializable objects
    with pytest.raises(TypeError, match="is not JSON serializable"):
        json.dumps({"d": d}, cls=CustomJSONEncoder)


def test_custom_json_encoder_handles_builtin():
    data = {"a": 1, "b": [1, 2, 3]}
    encoded = json.dumps(data, cls=CustomJSONEncoder)
    assert "a" in encoded and "b" in encoded
    assert "1" in encoded
