"""
Tests for the model registry functionality.
"""

from specsmith.model_optimizer import get_model_recommendations, optimize_for_model
from specsmith.model_registry import MODEL_REGISTRY, ModelProfile, get_model_profile, list_models


def test_model_registry_exists():
    """Test that the model registry exists and has entries."""
    assert MODEL_REGISTRY is not None
    assert len(MODEL_REGISTRY) > 0


def test_qwen_model_profile():
    """Test that the Qwen model profile is correctly defined."""
    profile = get_model_profile("Qwen3.6-35B-A3B")
    assert profile is not None
    assert profile.name == "Qwen3.6-35B-A3B"
    assert profile.provider == "Qwen"
    assert profile.context_length == 128000
    assert profile.cost_per_million_input_tokens == 0.01
    assert profile.cost_per_million_output_tokens == 0.03
    assert profile.recommended_runtime == "vLLM"
    assert profile.recommended_temperature == 0.7
    assert "large" in profile.tags
    assert "reasoning" in profile.tags
    assert profile.supports_function_calling is True
    assert profile.supports_json_output is True
    assert profile.supports_tools is True


def test_llama70b_model_profile():
    """Test that the Llama 3 70B model profile is correctly defined."""
    profile = get_model_profile("meta-llama/Meta-Llama-3-70B")
    assert profile is not None
    assert profile.name == "meta-llama/Meta-Llama-3-70B"
    assert profile.provider == "Hugging Face"
    assert profile.context_length == 8192
    assert profile.cost_per_million_input_tokens == 0.0
    assert profile.cost_per_million_output_tokens == 0.0
    assert profile.recommended_runtime == "vLLM"
    assert profile.recommended_temperature == 0.7
    assert "large" in profile.tags
    assert profile.supports_function_calling is True
    assert profile.supports_json_output is True
    assert profile.supports_tools is True


def test_llama8b_model_profile():
    """Test that the Llama 3 8B model profile is correctly defined."""
    profile = get_model_profile("meta-llama/Meta-Llama-3-8B")
    assert profile is not None
    assert profile.name == "meta-llama/Meta-Llama-3-8B"
    assert profile.provider == "Hugging Face"
    assert profile.context_length == 8192
    assert profile.cost_per_million_input_tokens == 0.0
    assert profile.cost_per_million_output_tokens == 0.0
    assert profile.recommended_runtime == "vLLM"
    assert profile.recommended_temperature == 0.7
    assert "medium" in profile.tags
    assert profile.supports_function_calling is True
    assert profile.supports_json_output is True
    assert profile.supports_tools is True


def test_mistral_model_profile():
    """Test that the Mistral model profile is correctly defined."""
    profile = get_model_profile("mistralai/Mistral-7B-v0.3")
    assert profile is not None
    assert profile.name == "mistralai/Mistral-7B-v0.3"
    assert profile.provider == "Hugging Face"
    assert profile.context_length == 32768
    assert profile.cost_per_million_input_tokens == 0.0
    assert profile.cost_per_million_output_tokens == 0.0
    assert profile.recommended_runtime == "vLLM"
    assert profile.recommended_temperature == 0.7
    assert "medium" in profile.tags
    assert profile.supports_function_calling is True
    assert profile.supports_json_output is True
    assert profile.supports_tools is True


def test_gemma_model_profile():
    """Test that the Gemma model profile is correctly defined."""
    profile = get_model_profile("google/gemma-2-27b")
    assert profile is not None
    assert profile.name == "google/gemma-2-27b"
    assert profile.provider == "Hugging Face"
    assert profile.context_length == 8192
    assert profile.cost_per_million_input_tokens == 0.0
    assert profile.cost_per_million_output_tokens == 0.0
    assert profile.recommended_runtime == "vLLM"
    assert profile.recommended_temperature == 0.7
    assert "large" in profile.tags
    assert profile.supports_function_calling is True
    assert profile.supports_json_output is True
    assert profile.supports_tools is True


def test_phi3_model_profile():
    """Test that the Phi-3 model profile is correctly defined."""
    profile = get_model_profile("microsoft/Phi-3-medium-128k")
    assert profile is not None
    assert profile.name == "microsoft/Phi-3-medium-128k"
    assert profile.provider == "Hugging Face"
    assert profile.context_length == 128000
    assert profile.cost_per_million_input_tokens == 0.0
    assert profile.cost_per_million_output_tokens == 0.0
    assert profile.recommended_runtime == "vLLM"
    assert profile.recommended_temperature == 0.7
    assert "medium" in profile.tags
    assert profile.supports_function_calling is True
    assert profile.supports_json_output is True
    assert profile.supports_tools is True


def test_list_models():
    """Test that we can list all available models."""
    models = list_models()
    assert len(models) > 0
    assert "Qwen3.6-35B-A3B" in models
    assert "meta-llama/Meta-Llama-3-70B" in models
    assert "meta-llama/Meta-Llama-3-8B" in models
    assert "mistralai/Mistral-7B-v0.3" in models
    assert "google/gemma-2-27b" in models
    assert "microsoft/Phi-3-medium-128k" in models
    # Test new models
    assert "meta-llama/Llama-3.2-1B" in models
    assert "meta-llama/Llama-3.2-3B" in models
    assert "meta-llama/Llama-3.1-8B" in models
    assert "meta-llama/Llama-3.1-70B" in models
    assert "mistralai/Mistral-7B-Instruct-v0.3" in models
    assert "mistralai/Mistral-8x7B-v0.3" in models
    assert "google/gemma-2-9b" in models
    assert "google/gemma-2-27b" in models
    assert "microsoft/Phi-3-mini-128k" in models
    assert "microsoft/Phi-3-small-128k" in models
    assert "Qwen/Qwen3-7B" in models
    assert "Qwen/Qwen3-32B" in models
    assert "openai/gpt-4" in models
    assert "openai/gpt-4-turbo" in models
    assert "openai/gpt-3.5-turbo" in models
    assert "anthropic/claude-3-opus" in models
    assert "anthropic/claude-3-sonnet" in models
    assert "anthropic/claude-3-haiku" in models
    assert "google/gemini-pro" in models
    assert "google/gemini-1.5-pro" in models
    assert "google/gemini-1.5-flash" in models
    assert "meta-llama/Llama-3.3-70B" in models
    assert "meta-llama/Llama-3.3-8B" in models
    assert "mistralai/Mistral-Large" in models
    assert "google/gemma-2-9b-it" in models
    assert "microsoft/Phi-3.5-mini" in models
    assert "microsoft/Phi-3.5-small" in models
    assert "Qwen/Qwen3-72B" in models
    assert "meta-llama/Llama-3.2-1B-Instruct" in models
    assert "meta-llama/Llama-3.2-3B-Instruct" in models
    assert "meta-llama/Llama-3.1-8B-Instruct" in models
    assert "mistralai/Mistral-7B-v0.3-Instruct" in models
    assert "google/gemma-2-27b-it" in models
    assert "microsoft/Phi-3.5-medium-128k" in models
    assert "meta-llama/Llama-3.3-70B-Instruct" in models
    assert "meta-llama/Llama-3.3-8B-Instruct" in models
    assert "Qwen/Qwen3-7B-Instruct" in models
    assert "Qwen/Qwen3-32B-Instruct" in models
    assert "Qwen/Qwen3-72B-Instruct" in models


def test_optimize_for_model():
    """Test model optimization functionality."""
    # Test with Qwen model
    params = optimize_for_model("Qwen3.6-35B-A3B", "general")
    assert "temperature" in params
    assert params["temperature"] == 0.7

    # Test with coding task
    params = optimize_for_model("Qwen3.6-35B-A3B", "coding")
    assert "temperature" in params
    # Should be lower for coding tasks
    assert params["temperature"] <= 0.3

    # Test with unknown model
    params = optimize_for_model("unknown-model", "general")
    assert "temperature" in params
    # Should default to 0.7
    assert params["temperature"] == 0.7


def test_get_model_recommendations():
    """Test skill recommendations based on model."""
    # Test with Qwen model
    recommendations = get_model_recommendations("Qwen3.6-35B-A3B", "coding")
    # Should recommend function calling and other relevant skills
    assert "function-caller" in recommendations or len(recommendations) > 0

    # Test with unknown model
    recommendations = get_model_recommendations("unknown-model", "general")
    assert isinstance(recommendations, list)


def test_model_profile_dataclass():
    """Test that ModelProfile dataclass works correctly."""
    profile = ModelProfile(
        name="Test Model",
        provider="Test Provider",
        context_length=1000,
        cost_per_million_input_tokens=0.1,
        cost_per_million_output_tokens=0.2,
        recommended_runtime="test",
        recommended_temperature=0.5,
        tags=["test", "model"],
        description="A test model profile"
    )

    assert profile.name == "Test Model"
    assert profile.provider == "Test Provider"
    assert profile.context_length == 1000
    assert profile.cost_per_million_input_tokens == 0.1
    assert profile.cost_per_million_output_tokens == 0.2
    assert profile.recommended_runtime == "test"
    assert profile.recommended_temperature == 0.5
    assert profile.tags == ["test", "model"]
    assert profile.description == "A test model profile"


# Test a few new models to ensure they're properly defined
def test_llama_3_2_1b_model_profile():
    """Test that the Llama 3.2 1B model profile is correctly defined."""
    profile = get_model_profile("meta-llama/Llama-3.2-1B")
    assert profile is not None
    assert profile.name == "meta-llama/Llama-3.2-1B"
    assert profile.provider == "Hugging Face"
    assert profile.context_length == 8192
    assert profile.cost_per_million_input_tokens == 0.0
    assert profile.cost_per_million_output_tokens == 0.0
    assert profile.recommended_runtime == "vLLM"
    assert profile.recommended_temperature == 0.7
    assert "small" in profile.tags
    assert "fast" in profile.tags
    assert profile.supports_function_calling is True
    assert profile.supports_json_output is True
    assert profile.supports_tools is True


def test_gpt4_model_profile():
    """Test that the GPT-4 model profile is correctly defined."""
    profile = get_model_profile("openai/gpt-4")
    assert profile is not None
    assert profile.name == "openai/gpt-4"
    assert profile.provider == "OpenAI"
    assert profile.context_length == 128000
    assert profile.cost_per_million_input_tokens == 30.0
    assert profile.cost_per_million_output_tokens == 60.0
    assert profile.recommended_runtime == "OpenAI API"
    assert profile.recommended_temperature == 0.7
    assert "large" in profile.tags
    assert profile.supports_function_calling is True
    assert profile.supports_json_output is True
    assert profile.supports_tools is True
