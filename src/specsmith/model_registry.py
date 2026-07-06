"""
Model profile registry for Specsmith.

This module contains the registry of known models with their profiles,
including performance characteristics, cost estimates, and optimization
recommendations for different runtime environments.
"""

from dataclasses import dataclass


@dataclass
class ModelProfile:
    """Profile for a specific model with optimization characteristics."""

    name: str
    """The name of the model (e.g., 'Qwen3.6-35B-A3B')"""

    provider: str
    """The provider of the model (e.g., 'Qwen', 'OpenAI', 'Anthropic')"""

    context_length: int
    """Maximum context length in tokens"""

    cost_per_million_input_tokens: float
    """Cost per million input tokens (USD)"""

    cost_per_million_output_tokens: float
    """Cost per million output tokens (USD)"""

    recommended_runtime: str
    """Recommended runtime environment (vLLM, Ollama, LM Studio, llama.cpp)"""

    recommended_temperature: float
    """Recommended temperature for optimal performance"""

    tags: list[str]
    """Tags for categorizing the model (e.g., 'large', 'reasoning', 'cost-effective')"""

    description: str
    """Human-readable description of the model"""

    # Optional fields for advanced features
    supports_function_calling: bool = False
    """Whether the model supports function calling"""

    supports_json_output: bool = False
    """Whether the model supports JSON output formatting"""

    supports_tools: bool = False
    """Whether the model supports tool calling"""

    # Performance characteristics
    tokens_per_second: float | None = None
    """Average tokens per second for generation (if available)"""

    max_concurrent_requests: int | None = None
    """Maximum concurrent requests supported (if available)"""


# Registry of known model profiles
MODEL_REGISTRY: dict[str, ModelProfile] = {
    "Qwen3.6-35B-A3B": ModelProfile(
        name="Qwen3.6-35B-A3B",
        provider="Qwen",
        context_length=128000,
        cost_per_million_input_tokens=0.01,
        cost_per_million_output_tokens=0.03,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["large", "reasoning", "cost-effective", "multilingual"],
        description="Qwen3.6 35B parameter model with advanced reasoning capabilities and multilingual support.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=150.0,
        max_concurrent_requests=10
    ),
    "meta-llama/Meta-Llama-3-70B": ModelProfile(
        name="meta-llama/Meta-Llama-3-70B",
        provider="Hugging Face",
        context_length=8192,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["large", "reasoning", "open-source"],
        description="Meta Llama 3 70B parameter model, one of the most capable open-source models.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=120.0,
        max_concurrent_requests=5
    ),
    "meta-llama/Meta-Llama-3-8B": ModelProfile(
        name="meta-llama/Meta-Llama-3-8B",
        provider="Hugging Face",
        context_length=8192,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["medium", "reasoning", "open-source"],
        description="Meta Llama 3 8B parameter model, efficient and capable for many tasks.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=200.0,
        max_concurrent_requests=10
    ),
    "mistralai/Mistral-7B-v0.3": ModelProfile(
        name="mistralai/Mistral-7B-v0.3",
        provider="Hugging Face",
        context_length=32768,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["medium", "reasoning", "open-source"],
        description="Mistral 7B model with strong performance and efficiency.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=180.0,
        max_concurrent_requests=8
    ),
    "google/gemma-2-27b": ModelProfile(
        name="google/gemma-2-27b",
        provider="Hugging Face",
        context_length=8192,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["large", "reasoning", "open-source"],
        description="Google Gemma 2 27B model with strong reasoning capabilities.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=160.0,
        max_concurrent_requests=6
    ),
    "microsoft/Phi-3-medium-128k": ModelProfile(
        name="microsoft/Phi-3-medium-128k",
        provider="Hugging Face",
        context_length=128000,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["medium", "reasoning", "open-source"],
        description="Microsoft Phi-3 medium model with long context window.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=140.0,
        max_concurrent_requests=7
    ),
    # Popular Hugging Face models based on downloads
    "meta-llama/Llama-3.2-1B": ModelProfile(
        name="meta-llama/Llama-3.2-1B",
        provider="Hugging Face",
        context_length=8192,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["small", "reasoning", "open-source", "fast"],
        description="Meta Llama 3.2 1B parameter model, optimized for speed and efficiency.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=250.0,
        max_concurrent_requests=15
    ),
    "meta-llama/Llama-3.2-3B": ModelProfile(
        name="meta-llama/Llama-3.2-3B",
        provider="Hugging Face",
        context_length=8192,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["medium", "reasoning", "open-source"],
        description="Meta Llama 3.2 3B parameter model, good balance of performance and efficiency.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=220.0,
        max_concurrent_requests=12
    ),
    "meta-llama/Llama-3.1-8B": ModelProfile(
        name="meta-llama/Llama-3.1-8B",
        provider="Hugging Face",
        context_length=8192,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["medium", "reasoning", "open-source"],
        description="Meta Llama 3.1 8B parameter model, optimized for reasoning and chat.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=200.0,
        max_concurrent_requests=10
    ),
    "meta-llama/Llama-3.1-70B": ModelProfile(
        name="meta-llama/Llama-3.1-70B",
        provider="Hugging Face",
        context_length=8192,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["large", "reasoning", "open-source"],
        description="Meta Llama 3.1 70B parameter model, one of the most capable open-source models.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=120.0,
        max_concurrent_requests=5
    ),
    "mistralai/Mistral-7B-Instruct-v0.3": ModelProfile(
        name="mistralai/Mistral-7B-Instruct-v0.3",
        provider="Hugging Face",
        context_length=32768,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["medium", "reasoning", "open-source", "instruction-tuned"],
        description="Mistral 7B instruction-tuned model with strong performance.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=180.0,
        max_concurrent_requests=8
    ),
    "mistralai/Mistral-8x7B-v0.3": ModelProfile(
        name="mistralai/Mistral-8x7B-v0.3",
        provider="Hugging Face",
        context_length=32768,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["large", "reasoning", "open-source", "multi-query"],
        description="Mistral 8x7B model with 56B parameters, optimized for multi-query tasks.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=100.0,
        max_concurrent_requests=4
    ),
    "google/gemma-2-9b": ModelProfile(
        name="google/gemma-2-9b",
        provider="Hugging Face",
        context_length=8192,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["medium", "reasoning", "open-source"],
        description="Google Gemma 2 9B parameter model with strong reasoning capabilities.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=190.0,
        max_concurrent_requests=10
    ),
    "google/gemma-2-27b": ModelProfile(
        name="google/gemma-2-27b",
        provider="Hugging Face",
        context_length=8192,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["large", "reasoning", "open-source"],
        description="Google Gemma 2 27B parameter model with strong reasoning capabilities.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=160.0,
        max_concurrent_requests=6
    ),
    "microsoft/Phi-3-mini-128k": ModelProfile(
        name="microsoft/Phi-3-mini-128k",
        provider="Hugging Face",
        context_length=128000,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["small", "reasoning", "open-source", "fast"],
        description="Microsoft Phi-3 mini model with long context window and fast performance.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=240.0,
        max_concurrent_requests=12
    ),
    "microsoft/Phi-3-small-128k": ModelProfile(
        name="microsoft/Phi-3-small-128k",
        provider="Hugging Face",
        context_length=128000,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["medium", "reasoning", "open-source"],
        description="Microsoft Phi-3 small model with long context window.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=180.0,
        max_concurrent_requests=8
    ),
    "Qwen/Qwen3-7B": ModelProfile(
        name="Qwen/Qwen3-7B",
        provider="Qwen",
        context_length=32768,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["medium", "reasoning", "multilingual"],
        description="Qwen3 7B parameter model with strong multilingual capabilities.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=170.0,
        max_concurrent_requests=10
    ),
    "Qwen/Qwen3-32B": ModelProfile(
        name="Qwen/Qwen3-32B",
        provider="Qwen",
        context_length=32768,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["large", "reasoning", "multilingual"],
        description="Qwen3 32B parameter model with advanced reasoning capabilities.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=140.0,
        max_concurrent_requests=8
    ),
    "openai/gpt-4": ModelProfile(
        name="openai/gpt-4",
        provider="OpenAI",
        context_length=128000,
        cost_per_million_input_tokens=30.0,
        cost_per_million_output_tokens=60.0,
        recommended_runtime="OpenAI API",
        recommended_temperature=0.7,
        tags=["large", "reasoning", "api"],
        description="OpenAI GPT-4 model with advanced reasoning capabilities.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=80.0,
        max_concurrent_requests=2
    ),
    "openai/gpt-4-turbo": ModelProfile(
        name="openai/gpt-4-turbo",
        provider="OpenAI",
        context_length=128000,
        cost_per_million_input_tokens=10.0,
        cost_per_million_output_tokens=30.0,
        recommended_runtime="OpenAI API",
        recommended_temperature=0.7,
        tags=["large", "reasoning", "api", "cost-effective"],
        description="OpenAI GPT-4 Turbo model with improved performance and cost efficiency.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=100.0,
        max_concurrent_requests=3
    ),
    "openai/gpt-3.5-turbo": ModelProfile(
        name="openai/gpt-3.5-turbo",
        provider="OpenAI",
        context_length=16385,
        cost_per_million_input_tokens=0.5,
        cost_per_million_output_tokens=1.5,
        recommended_runtime="OpenAI API",
        recommended_temperature=0.7,
        tags=["medium", "reasoning", "api", "cost-effective"],
        description="OpenAI GPT-3.5 Turbo model, fast and cost-effective for many tasks.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=150.0,
        max_concurrent_requests=5
    ),
    "anthropic/claude-3-opus": ModelProfile(
        name="anthropic/claude-3-opus",
        provider="Anthropic",
        context_length=200000,
        cost_per_million_input_tokens=15.0,
        cost_per_million_output_tokens=75.0,
        recommended_runtime="Anthropic API",
        recommended_temperature=0.7,
        tags=["large", "reasoning", "api", "creative"],
        description="Anthropic Claude 3 Opus model with advanced reasoning and creativity.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=60.0,
        max_concurrent_requests=2
    ),
    "anthropic/claude-3-sonnet": ModelProfile(
        name="anthropic/claude-3-sonnet",
        provider="Anthropic",
        context_length=200000,
        cost_per_million_input_tokens=3.0,
        cost_per_million_output_tokens=15.0,
        recommended_runtime="Anthropic API",
        recommended_temperature=0.7,
        tags=["large", "reasoning", "api", "balanced"],
        description="Anthropic Claude 3 Sonnet model with balanced performance and cost.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=80.0,
        max_concurrent_requests=3
    ),
    "anthropic/claude-3-haiku": ModelProfile(
        name="anthropic/claude-3-haiku",
        provider="Anthropic",
        context_length=200000,
        cost_per_million_input_tokens=0.25,
        cost_per_million_output_tokens=1.25,
        recommended_runtime="Anthropic API",
        recommended_temperature=0.7,
        tags=["small", "reasoning", "api", "fast"],
        description="Anthropic Claude 3 Haiku model with fast response times.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=200.0,
        max_concurrent_requests=10
    ),
    # Frontier models with high performance
    "google/gemini-pro": ModelProfile(
        name="google/gemini-pro",
        provider="Google",
        context_length=32768,
        cost_per_million_input_tokens=0.5,
        cost_per_million_output_tokens=1.5,
        recommended_runtime="Google API",
        recommended_temperature=0.7,
        tags=["large", "reasoning", "api", "multimodal"],
        description="Google Gemini Pro model with multimodal capabilities.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=120.0,
        max_concurrent_requests=4
    ),
    "google/gemini-1.5-pro": ModelProfile(
        name="google/gemini-1.5-pro",
        provider="Google",
        context_length=200000,
        cost_per_million_input_tokens=1.0,
        cost_per_million_output_tokens=3.0,
        recommended_runtime="Google API",
        recommended_temperature=0.7,
        tags=["large", "reasoning", "api", "multimodal"],
        description="Google Gemini 1.5 Pro model with enhanced capabilities.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=100.0,
        max_concurrent_requests=3
    ),
    "google/gemini-1.5-flash": ModelProfile(
        name="google/gemini-1.5-flash",
        provider="Google",
        context_length=100000,
        cost_per_million_input_tokens=0.075,
        cost_per_million_output_tokens=0.3,
        recommended_runtime="Google API",
        recommended_temperature=0.7,
        tags=["medium", "reasoning", "api", "fast"],
        description="Google Gemini 1.5 Flash model with fast response times.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=250.0,
        max_concurrent_requests=8
    ),
    "meta-llama/Llama-3.3-70B": ModelProfile(
        name="meta-llama/Llama-3.3-70B",
        provider="Hugging Face",
        context_length=128000,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["large", "reasoning", "open-source"],
        description="Meta Llama 3.3 70B parameter model, latest iteration with improved performance.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=110.0,
        max_concurrent_requests=5
    ),
    "meta-llama/Llama-3.3-8B": ModelProfile(
        name="meta-llama/Llama-3.3-8B",
        provider="Hugging Face",
        context_length=8192,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["medium", "reasoning", "open-source"],
        description="Meta Llama 3.3 8B parameter model, optimized for efficiency.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=210.0,
        max_concurrent_requests=10
    ),
    "mistralai/Mistral-Large": ModelProfile(
        name="mistralai/Mistral-Large",
        provider="Hugging Face",
        context_length=32768,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["large", "reasoning", "open-source"],
        description="Mistral Large model with strong reasoning capabilities.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=130.0,
        max_concurrent_requests=6
    ),
    "google/gemma-2-9b-it": ModelProfile(
        name="google/gemma-2-9b-it",
        provider="Hugging Face",
        context_length=8192,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["medium", "reasoning", "open-source", "instruction-tuned"],
        description="Google Gemma 2 9B instruction-tuned model with strong performance.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=190.0,
        max_concurrent_requests=10
    ),
    "microsoft/Phi-3.5-mini": ModelProfile(
        name="microsoft/Phi-3.5-mini",
        provider="Hugging Face",
        context_length=128000,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["small", "reasoning", "open-source", "fast"],
        description="Microsoft Phi-3.5 mini model with improved performance and speed.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=260.0,
        max_concurrent_requests=15
    ),
    "microsoft/Phi-3.5-small": ModelProfile(
        name="microsoft/Phi-3.5-small",
        provider="Hugging Face",
        context_length=128000,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["medium", "reasoning", "open-source"],
        description="Microsoft Phi-3.5 small model with balanced performance.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=190.0,
        max_concurrent_requests=10
    ),
    "Qwen/Qwen3-72B": ModelProfile(
        name="Qwen/Qwen3-72B",
        provider="Qwen",
        context_length=32768,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["large", "reasoning", "multilingual"],
        description="Qwen3 72B parameter model with advanced reasoning capabilities.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=130.0,
        max_concurrent_requests=8
    ),
    "meta-llama/Llama-3.2-1B-Instruct": ModelProfile(
        name="meta-llama/Llama-3.2-1B-Instruct",
        provider="Hugging Face",
        context_length=8192,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["small", "reasoning", "open-source", "instruction-tuned"],
        description="Meta Llama 3.2 1B instruction-tuned model optimized for chat.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=250.0,
        max_concurrent_requests=15
    ),
    "meta-llama/Llama-3.2-3B-Instruct": ModelProfile(
        name="meta-llama/Llama-3.2-3B-Instruct",
        provider="Hugging Face",
        context_length=8192,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["medium", "reasoning", "open-source", "instruction-tuned"],
        description="Meta Llama 3.2 3B instruction-tuned model with good performance.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=220.0,
        max_concurrent_requests=12
    ),
    "meta-llama/Llama-3.1-8B-Instruct": ModelProfile(
        name="meta-llama/Llama-3.1-8B-Instruct",
        provider="Hugging Face",
        context_length=8192,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["medium", "reasoning", "open-source", "instruction-tuned"],
        description="Meta Llama 3.1 8B instruction-tuned model optimized for chat.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=200.0,
        max_concurrent_requests=10
    ),
    "mistralai/Mistral-7B-v0.3-Instruct": ModelProfile(
        name="mistralai/Mistral-7B-v0.3-Instruct",
        provider="Hugging Face",
        context_length=32768,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["medium", "reasoning", "open-source", "instruction-tuned"],
        description="Mistral 7B instruction-tuned model with strong performance.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=180.0,
        max_concurrent_requests=8
    ),
    "google/gemma-2-27b-it": ModelProfile(
        name="google/gemma-2-27b-it",
        provider="Hugging Face",
        context_length=8192,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["large", "reasoning", "open-source", "instruction-tuned"],
        description="Google Gemma 2 27B instruction-tuned model with strong reasoning.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=160.0,
        max_concurrent_requests=6
    ),
    "microsoft/Phi-3.5-medium-128k": ModelProfile(
        name="microsoft/Phi-3.5-medium-128k",
        provider="Hugging Face",
        context_length=128000,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["medium", "reasoning", "open-source"],
        description="Microsoft Phi-3.5 medium model with long context window.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=180.0,
        max_concurrent_requests=8
    ),
    "meta-llama/Llama-3.3-70B-Instruct": ModelProfile(
        name="meta-llama/Llama-3.3-70B-Instruct",
        provider="Hugging Face",
        context_length=128000,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["large", "reasoning", "open-source", "instruction-tuned"],
        description="Meta Llama 3.3 70B instruction-tuned model with improved performance.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=110.0,
        max_concurrent_requests=5
    ),
    "meta-llama/Llama-3.3-8B-Instruct": ModelProfile(
        name="meta-llama/Llama-3.3-8B-Instruct",
        provider="Hugging Face",
        context_length=8192,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["medium", "reasoning", "open-source", "instruction-tuned"],
        description="Meta Llama 3.3 8B instruction-tuned model optimized for efficiency.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=210.0,
        max_concurrent_requests=10
    ),
    "Qwen/Qwen3-7B-Instruct": ModelProfile(
        name="Qwen/Qwen3-7B-Instruct",
        provider="Qwen",
        context_length=32768,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["medium", "reasoning", "multilingual", "instruction-tuned"],
        description="Qwen3 7B instruction-tuned model with strong multilingual capabilities.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=170.0,
        max_concurrent_requests=10
    ),
    "Qwen/Qwen3-32B-Instruct": ModelProfile(
        name="Qwen/Qwen3-32B-Instruct",
        provider="Qwen",
        context_length=32768,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["large", "reasoning", "multilingual", "instruction-tuned"],
        description="Qwen3 32B instruction-tuned model with advanced reasoning capabilities.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=140.0,
        max_concurrent_requests=8
    ),
    "Qwen/Qwen3-72B-Instruct": ModelProfile(
        name="Qwen/Qwen3-72B-Instruct",
        provider="Qwen",
        context_length=32768,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["large", "reasoning", "multilingual", "instruction-tuned"],
        description="Qwen3 72B instruction-tuned model with advanced reasoning capabilities.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=130.0,
        max_concurrent_requests=8
    ),
    # Additional popular Hugging Face models
    "meta-llama/Llama-3.2-11B-Vision": ModelProfile(
        name="meta-llama/Llama-3.2-11B-Vision",
        provider="Hugging Face",
        context_length=128000,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["medium", "vision", "open-source", "multimodal"],
        description="Meta Llama 3.2 11B Vision model with multimodal capabilities.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=150.0,
        max_concurrent_requests=8
    ),
    "meta-llama/Llama-3.2-90B-Vision": ModelProfile(
        name="meta-llama/Llama-3.2-90B-Vision",
        provider="Hugging Face",
        context_length=128000,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["large", "vision", "open-source", "multimodal"],
        description="Meta Llama 3.2 90B Vision model with advanced multimodal capabilities.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=100.0,
        max_concurrent_requests=5
    ),
    "mistralai/Mistral-7B-v0.3-Instruct": ModelProfile(
        name="mistralai/Mistral-7B-v0.3-Instruct",
        provider="Hugging Face",
        context_length=32768,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["medium", "reasoning", "open-source", "instruction-tuned"],
        description="Mistral 7B instruction-tuned model with strong performance.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=180.0,
        max_concurrent_requests=8
    ),
    "google/gemma-2-9b-it": ModelProfile(
        name="google/gemma-2-9b-it",
        provider="Hugging Face",
        context_length=8192,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["medium", "reasoning", "open-source", "instruction-tuned"],
        description="Google Gemma 2 9B instruction-tuned model with strong performance.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=190.0,
        max_concurrent_requests=10
    ),
    "google/gemma-2-27b-it": ModelProfile(
        name="google/gemma-2-27b-it",
        provider="Hugging Face",
        context_length=8192,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["large", "reasoning", "open-source", "instruction-tuned"],
        description="Google Gemma 2 27B instruction-tuned model with strong reasoning.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=160.0,
        max_concurrent_requests=6
    ),
    "microsoft/Phi-3.5-mini": ModelProfile(
        name="microsoft/Phi-3.5-mini",
        provider="Hugging Face",
        context_length=128000,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["small", "reasoning", "open-source", "fast"],
        description="Microsoft Phi-3.5 mini model with improved performance and speed.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=260.0,
        max_concurrent_requests=15
    ),
    "microsoft/Phi-3.5-small": ModelProfile(
        name="microsoft/Phi-3.5-small",
        provider="Hugging Face",
        context_length=128000,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["medium", "reasoning", "open-source"],
        description="Microsoft Phi-3.5 small model with balanced performance.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=190.0,
        max_concurrent_requests=10
    ),
    "microsoft/Phi-3.5-medium-128k": ModelProfile(
        name="microsoft/Phi-3.5-medium-128k",
        provider="Hugging Face",
        context_length=128000,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["medium", "reasoning", "open-source"],
        description="Microsoft Phi-3.5 medium model with long context window.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=180.0,
        max_concurrent_requests=8
    ),
    # Popular open-source models with high download counts
    "meta-llama/Llama-3.3-70B-Instruct": ModelProfile(
        name="meta-llama/Llama-3.3-70B-Instruct",
        provider="Hugging Face",
        context_length=128000,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["large", "reasoning", "open-source", "instruction-tuned"],
        description="Meta Llama 3.3 70B instruction-tuned model with improved performance.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=110.0,
        max_concurrent_requests=5
    ),
    "meta-llama/Llama-3.3-8B-Instruct": ModelProfile(
        name="meta-llama/Llama-3.3-8B-Instruct",
        provider="Hugging Face",
        context_length=8192,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["medium", "reasoning", "open-source", "instruction-tuned"],
        description="Meta Llama 3.3 8B instruction-tuned model optimized for efficiency.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=210.0,
        max_concurrent_requests=10
    ),
    "Qwen/Qwen3-72B-Instruct": ModelProfile(
        name="Qwen/Qwen3-72B-Instruct",
        provider="Qwen",
        context_length=32768,
        cost_per_million_input_tokens=0.0,
        cost_per_million_output_tokens=0.0,
        recommended_runtime="vLLM",
        recommended_temperature=0.7,
        tags=["large", "reasoning", "multilingual", "instruction-tuned"],
        description="Qwen3 72B instruction-tuned model with advanced reasoning capabilities.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=130.0,
        max_concurrent_requests=8
    ),
    # Frontier models with high performance
    "google/gemini-2.0-flash": ModelProfile(
        name="google/gemini-2.0-flash",
        provider="Google",
        context_length=1000000,
        cost_per_million_input_tokens=0.075,
        cost_per_million_output_tokens=0.3,
        recommended_runtime="Google API",
        recommended_temperature=0.7,
        tags=["medium", "reasoning", "api", "fast"],
        description="Google Gemini 2.0 Flash model with enhanced capabilities and speed.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=300.0,
        max_concurrent_requests=10
    ),
    "google/gemini-2.0-pro": ModelProfile(
        name="google/gemini-2.0-pro",
        provider="Google",
        context_length=2000000,
        cost_per_million_input_tokens=1.0,
        cost_per_million_output_tokens=3.0,
        recommended_runtime="Google API",
        recommended_temperature=0.7,
        tags=["large", "reasoning", "api", "multimodal"],
        description="Google Gemini 2.0 Pro model with advanced multimodal capabilities.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=150.0,
        max_concurrent_requests=5
    ),
    "openai/gpt-4o": ModelProfile(
        name="openai/gpt-4o",
        provider="OpenAI",
        context_length=128000,
        cost_per_million_input_tokens=5.0,
        cost_per_million_output_tokens=15.0,
        recommended_runtime="OpenAI API",
        recommended_temperature=0.7,
        tags=["large", "reasoning", "api", "multimodal"],
        description="OpenAI GPT-4o model with advanced multimodal capabilities.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=120.0,
        max_concurrent_requests=3
    ),
    "openai/gpt-4o-mini": ModelProfile(
        name="openai/gpt-4o-mini",
        provider="OpenAI",
        context_length=128000,
        cost_per_million_input_tokens=0.15,
        cost_per_million_output_tokens=0.6,
        recommended_runtime="OpenAI API",
        recommended_temperature=0.7,
        tags=["small", "reasoning", "api", "fast"],
        description="OpenAI GPT-4o mini model with fast response times.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=200.0,
        max_concurrent_requests=8
    ),
    "anthropic/claude-3-5-sonnet": ModelProfile(
        name="anthropic/claude-3-5-sonnet",
        provider="Anthropic",
        context_length=200000,
        cost_per_million_input_tokens=3.0,
        cost_per_million_output_tokens=15.0,
        recommended_runtime="Anthropic API",
        recommended_temperature=0.7,
        tags=["large", "reasoning", "api", "balanced"],
        description="Anthropic Claude 3.5 Sonnet model with enhanced performance.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=90.0,
        max_concurrent_requests=4
    ),
    "anthropic/claude-3-5-haiku": ModelProfile(
        name="anthropic/claude-3-5-haiku",
        provider="Anthropic",
        context_length=200000,
        cost_per_million_input_tokens=0.25,
        cost_per_million_output_tokens=1.25,
        recommended_runtime="Anthropic API",
        recommended_temperature=0.7,
        tags=["small", "reasoning", "api", "fast"],
        description="Anthropic Claude 3.5 Haiku model with improved speed.",
        supports_function_calling=True,
        supports_json_output=True,
        supports_tools=True,
        tokens_per_second=250.0,
        max_concurrent_requests=12
    )
}


def get_model_profile(model_name: str) -> ModelProfile | None:
    """
    Get a model profile by name.

    Args:
        model_name: The name of the model

    Returns:
        The model profile if found, None otherwise
    """
    return MODEL_REGISTRY.get(model_name)


def list_models() -> list[str]:
    """
    List all available model names in the registry.

    Returns:
        List of model names
    """
    return list(MODEL_REGISTRY.keys())


def add_model_profile(profile: ModelProfile) -> None:
    """
    Add a new model profile to the registry.

    Args:
        profile: The model profile to add
    """
    MODEL_REGISTRY[profile.name] = profile


def remove_model_profile(model_name: str) -> bool:
    """
    Remove a model profile from the registry.

    Args:
        model_name: The name of the model to remove

    Returns:
        True if removed, False if not found
    """
    if model_name in MODEL_REGISTRY:
        del MODEL_REGISTRY[model_name]
        return True
    return False


# For backward compatibility
def get_model_profiles() -> dict[str, ModelProfile]:
    """
    Get all model profiles (alias for MODEL_REGISTRY).

    Returns:
        Dictionary of all model profiles
    """
    return MODEL_REGISTRY


# Example usage:
# profile = get_model_profile("Qwen3.6-35B-A3B")
# print(profile.name)
# print(profile.provider)
# print(profile.context_length)
