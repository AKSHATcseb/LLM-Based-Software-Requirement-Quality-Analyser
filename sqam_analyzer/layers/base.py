"""
sqam_analyzer.layers.base
~~~~~~~~~~~~~~~~~~~~~~~~~
Base abstractions for the 5-layer Software Requirement Quality Analyzer.
Provides lifecycle hooks, LLM invocation interfaces, and prompt management.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional
from sqam_analyzer.llm_provider import BaseLLMClient


class BaseLayer(ABC):
    """
    Abstract base class for each layer in the 5-layer pipeline.
    Ensures modularity, uniform telemetry, and swappable prompts.
    """

    def __init__(
        self,
        llm_client: BaseLLMClient,
        system_prompt: Optional[str] = None,
        user_prompt_template: Optional[str] = None,
    ):
        self.llm_client = llm_client
        self._system_prompt = system_prompt
        self._user_prompt_template = user_prompt_template

    @property
    def system_prompt(self) -> str:
        """Returns the configured or default system prompt."""
        if self._system_prompt is not None:
            return self._system_prompt
        return self.get_default_system_prompt()

    @property
    def user_prompt_template(self) -> str:
        """Returns the configured or default user prompt template."""
        if self._user_prompt_template is not None:
            return self._user_prompt_template
        return self.get_default_user_prompt_template()

    @abstractmethod
    def get_default_system_prompt(self) -> str:
        """Subclasses must define their default system prompt."""
        pass

    @abstractmethod
    def get_default_user_prompt_template(self) -> str:
        """Subclasses must define their default user prompt template."""
        pass

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Subclasses must implement their layer-specific execution logic."""
        pass
