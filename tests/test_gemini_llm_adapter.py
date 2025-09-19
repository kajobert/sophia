from unittest.mock import patch, MagicMock, PropertyMock
from core.gemini_llm_adapter import GeminiLLMAdapter


def test_llm_adapter_initialization():
    """Testuje, zda se adaptér správně inicializuje."""
    with patch("google.generativeai.configure") as mock_configure, patch(
        "google.generativeai.GenerativeModel"
    ) as mock_model:
        adapter = GeminiLLMAdapter(model="test-model", api_key="test-key")

        mock_configure.assert_called_once_with(api_key="test-key")
        mock_model.assert_called_once_with("test-model")
        assert adapter.model_name == "test-model"


def test_llm_adapter_initialization_uses_env_var():
    """Testuje, zda adaptér použije API klíč z proměnných prostředí."""
    with patch("google.generativeai.configure") as mock_configure, patch(
        "google.generativeai.GenerativeModel"
    ), patch("os.getenv", return_value="env-key"):
        GeminiLLMAdapter(model="test-model")
        mock_configure.assert_called_once_with(api_key="env-key")


def test_llm_adapter_call_and_token_usage():
    """Testuje metodu _call, ověřuje volání Gemini API a sledování tokenů."""

    mock_api_response = MagicMock()
    mock_api_response.text = "Mocked response"
    mock_api_response.usage_metadata = {"total_tokens": 42}

    with patch("google.generativeai.configure"), patch(
        "google.generativeai.GenerativeModel"
    ) as mock_model_class:
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value = mock_api_response
        mock_model_class.return_value = mock_model_instance

        adapter = GeminiLLMAdapter(model="test-model", api_key="test-key")

        result = adapter.invoke("Test prompt")

        mock_model_instance.generate_content.assert_called_once()
        call_args, call_kwargs = mock_model_instance.generate_content.call_args
        assert call_args[0] == "Test prompt"

        assert result == "Mocked response"
        assert adapter.get_token_usage() == 42


def test_llm_adapter_call_handles_blocked_response():
    """Testuje, jak se adaptér chová, když je odpověď z API blokována."""
    mock_api_response = MagicMock()
    type(mock_api_response).text = PropertyMock(side_effect=ValueError)
    mock_api_response.prompt_feedback = "Safety reasons"
    mock_api_response.usage_metadata = {"total_tokens": 10}

    with patch("google.generativeai.configure"), patch(
        "google.generativeai.GenerativeModel"
    ) as mock_model_class:
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value = mock_api_response
        mock_model_class.return_value = mock_model_instance

        adapter = GeminiLLMAdapter(model="test-model", api_key="test-key")
        result = adapter.invoke("A potentially problematic prompt")

        assert "Error: Response from Gemini API was blocked" in result
        assert "Safety reasons" in result
        assert adapter.get_token_usage() == 10
