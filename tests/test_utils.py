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


def test_custom_json_encoder_handles_datetime():
    import datetime
    now = datetime.datetime.now()
    data = {"time": now}
    encoded = json.dumps(data, cls=CustomJSONEncoder)
    # The output should be a JSON string with the time in ISO format.
    # e.g., {"time": "2023-10-27T10:00:00.000000"}
    assert f'"time": "{now.isoformat()}"' in encoded
