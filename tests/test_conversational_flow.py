import pytest
from fastapi.testclient import TestClient
from web.api import app

# A more advanced mock for AdvancedMemory to use in our specific test
class StatefulMockAdvancedMemory:
    def __init__(self, config_path='config.yaml', user_id="sophia"):
        self.memories = []

    async def add_memory(self, content, mem_type, metadata=None):
        self.memories.append({'content': content, 'type': mem_type, 'metadata': metadata})
        return "mock_chat_id_stateful"

    async def read_last_n_memories(self, n=10, mem_type: str = None):
        if mem_type == 'CONVERSATION':
            return [mem.copy() for mem in self.memories if mem['type'] == 'CONVERSATION']
        return []

    def close(self):
        pass

@pytest.fixture
def stateful_memory_mock(monkeypatch):
    mock_instance = StatefulMockAdvancedMemory()
    monkeypatch.setattr("core.orchestrator.AdvancedMemory", lambda *args, **kwargs: mock_instance)
    return mock_instance

def test_conversational_flow_plumbing(stateful_memory_mock):
    """
    Tests the "plumbing" of the conversational flow.
    """
    with TestClient(app) as client:
        # --- First Request ---
        response1 = client.post("/chat", json={"prompt": "Kdo jsi?"})
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1['status'] == 'success'

        expected_response_part = "Here is the plan: A simple test plan for the user request."
        # The response is a CrewOutput object, we need to access the raw string via the .raw attribute.
        # The JSON response from FastAPI will have converted the CrewOutput object to a dict.
        assert expected_response_part in data1['final_context']['response']['raw']

        # Verify memory was written to
        assert len(stateful_memory_mock.memories) == 1
        assert stateful_memory_mock.memories[0]['type'] == 'CONVERSATION'
        assert "Kdo jsi?" in stateful_memory_mock.memories[0]['metadata']['prompt']
        # The object saved to metadata is the actual CrewOutput object.
        assert expected_response_part in stateful_memory_mock.memories[0]['metadata']['response'].raw
