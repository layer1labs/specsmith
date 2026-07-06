"""
Model-aware optimization system for Specsmith.

This module provides functionality to optimize agent behavior based on model characteristics
and runtime environment, including temperature adjustments, context length management,
and runtime-specific optimizations.
"""

from typing import Any

from .model_registry import ModelProfile, get_model_profile


class ModelOptimizer:
    """Handles model-aware optimizations for Specsmith agents."""

    def __init__(self) -> None:
        """Initialize the model optimizer."""
        self._model_profiles: dict[str, ModelProfile] = {}

    def get_optimized_parameters(
        self,
        model_name: str,
        task_type: str = "general",
        current_parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Get optimized parameters for a given model and task type.

        Args:
            model_name: Name of the model to optimize for
            task_type: Type of task (e.g., "reasoning", "coding", "summarization")
            current_parameters: Current parameter settings to build upon

        Returns:
            Dictionary of optimized parameters
        """
        if current_parameters is None:
            current_parameters = {}

        # Get model profile
        profile = get_model_profile(model_name)
        if not profile:
            # Return defaults if no profile found
            return self._get_default_parameters(task_type, current_parameters)

        # Start with current parameters
        optimized = current_parameters.copy()

        # Apply model-specific optimizations
        if profile.recommended_temperature is not None:
            optimized['temperature'] = profile.recommended_temperature

        # Apply task-specific optimizations
        optimized = self._apply_task_optimizations(task_type, profile, optimized)

        # Apply runtime-specific optimizations
        optimized = self._apply_runtime_optimizations(profile, optimized)

        return optimized

    def _get_default_parameters(
        self,
        task_type: str,
        current_parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """Get default parameters when no model profile is available."""
        optimized = current_parameters.copy()

        # Default temperature based on task type
        task_temperatures = {
            "reasoning": 0.7,
            "coding": 0.2,
            "summarization": 0.5,
            "general": 0.7
        }

        optimized['temperature'] = task_temperatures.get(task_type, 0.7)
        return optimized

    def _apply_task_optimizations(
        self,
        task_type: str,
        profile: ModelProfile,
        parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """Apply task-specific optimizations."""
        optimized = parameters.copy()

        # Adjust temperature based on task type
        if task_type == "coding" and profile.supports_function_calling:
            # Lower temperature for coding tasks
            optimized['temperature'] = min(0.3, optimized.get('temperature', 0.7))
        elif task_type == "reasoning":
            # Slightly higher temperature for reasoning
            optimized['temperature'] = min(0.8, optimized.get('temperature', 0.7))
        elif task_type == "summarization":
            # Moderate temperature for summarization
            optimized['temperature'] = min(0.6, optimized.get('temperature', 0.7))

        return optimized

    def _apply_runtime_optimizations(
        self,
        profile: ModelProfile,
        parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """Apply runtime-specific optimizations."""
        optimized = parameters.copy()

        # Context length optimization
        if profile.context_length:
            # Set context length to a reasonable value (e.g., 80% of max)
            optimized['max_context_length'] = int(profile.context_length * 0.8)

        # Runtime-specific settings
        if profile.recommended_runtime:
            optimized['runtime'] = profile.recommended_runtime

        return optimized

    def get_skill_recommendations(
        self,
        model_name: str,
        task_type: str = "general"
    ) -> list[str]:
        """
        Get recommended skills based on model characteristics and task type.

        Args:
            model_name: Name of the model
            task_type: Type of task

        Returns:
            List of recommended skill slugs
        """
        profile = get_model_profile(model_name)
        recommendations: list[str] = []

        if not profile:
            return recommendations

        # Add skills based on model capabilities
        if profile.supports_function_calling:
            recommendations.append("function-caller")

        if profile.supports_json_output:
            recommendations.append("json-output-formatter")

        if profile.supports_tools:
            recommendations.append("tool-caller")

        # Add task-specific skills
        if task_type == "coding":
            recommendations.append("code-generator")
            recommendations.append("code-analyzer")
        elif task_type == "reasoning":
            recommendations.append("logical-reasoner")
            recommendations.append("problem-solver")
        elif task_type == "summarization":
            recommendations.append("text-summarizer")

        return recommendations


# Global optimizer instance
model_optimizer = ModelOptimizer()


def optimize_for_model(
    model_name: str,
    task_type: str = "general",
    parameters: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Convenience function to get optimized parameters for a model and task.

    Args:
        model_name: Name of the model
        task_type: Type of task
        parameters: Current parameters to optimize

    Returns:
        Optimized parameters dictionary
    """
    return model_optimizer.get_optimized_parameters(model_name, task_type, parameters)


def get_model_recommendations(
    model_name: str,
    task_type: str = "general"
) -> list[str]:
    """
    Get recommended skills for a given model and task type.

    Args:
        model_name: Name of the model
        task_type: Type of task

    Returns:
        List of recommended skill slugs
    """
    return model_optimizer.get_skill_recommendations(model_name, task_type)
