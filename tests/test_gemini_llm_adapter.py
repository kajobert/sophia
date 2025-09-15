import pytest
from unittest.mock import patch, MagicMock
from core.gemini_llm_adapter import GeminiLLMAdapter

def test_llm_adapter_initialization():
    """Testuje, zda se adaptér správně inicializuje."""
    with patch('google.generativeai.configure') as mock_configure, \
         patch('google.generativeai.GenerativeModel') as mock_model:

        adapter = GeminiLLMAdapter(model="test-model", api_key="test-key")

        mock_configure.assert_called_once_with(api_key="test-key")
        mock_model.assert_called_once_with("test-model")
        assert adapter.model_name == "test-model"

def test_llm_adapter_initialization_uses_env_var():
    """Testuje, zda adaptér použije API klíč z proměnných prostředí."""
    with patch('google.generativeai.configure') as mock_configure, \
         patch('google.generativeai.GenerativeModel'), \
         patch('os.getenv', return_value="env-key"):

        adapter = GeminiLLMAdapter()
        mock_configure.assert_called_once_with(api_key="env-key")

def test_llm_adapter_call():
    """Testuje metodu _call a ověřuje, že volá správnou metodu Gemini API."""

    # Mock pro odpověď z Gemini
    mock_api_response = MagicMock()
    mock_api_response.text = "Mocked response"

    with patch('google.generativeai.configure'), \
         patch('google.generativeai.GenerativeModel') as mock_model_class:

        # Mock instance modelu, kterou vrací `GenerativeModel()`
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value = mock_api_response
        mock_model_class.return_value = mock_model_instance

        adapter = GeminiLLMAdapter(api_key="test-key")

        # Nyní voláme `invoke`, což je doporučená metoda pro LangChain LLM
        result = adapter.invoke("Test prompt")

        # Ověření, že byla volána správná metoda s správnými argumenty
        mock_model_instance.generate_content.assert_called_once()
        # První argument volání `generate_content` je prompt
        call_args, call_kwargs = mock_model_instance.generate_content.call_args
        assert call_args[0] == "Test prompt"

        assert result == "Mocked response"

from unittest.mock import patch, MagicMock, PropertyMock

def test_llm_adapter_call_handles_blocked_response():
    """Testuje, jak se adaptér chová, když je odpověď z API blokována."""
    mock_api_response = MagicMock()
    # Použití PropertyMock pro správnou simulaci chyby při přístupu k atributu .text
    type(mock_api_response).text = PropertyMock(side_effect=ValueError)
    mock_api_response.prompt_feedback = "Safety reasons"

    with patch('google.generativeai.configure'), \
         patch('google.generativeai.GenerativeModel') as mock_model_class:

        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value = mock_api_response
        mock_model_class.return_value = mock_model_instance

        adapter = GeminiLLMAdapter(api_key="test-key")
        result = adapter.invoke("A potentially problematic prompt")

        assert "Error: Response from Gemini API was blocked" in result
        assert "Safety reasons" in result
