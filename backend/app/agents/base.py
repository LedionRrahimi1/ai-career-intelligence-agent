"""Base agent abstraction: input → reason → tools → output."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

TIn = TypeVar("TIn")
TOut = TypeVar("TOut")

logger = logging.getLogger(__name__)


@dataclass
class AgentResult(Generic[TOut]):
    output: TOut
    reasoning: str = ""
    tools_used: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC, Generic[TIn, TOut]):
    """
    Every agent follows:
      1. receive input
      2. reason about the task
      3. invoke tools
      4. produce structured output
    """

    name: str = "base_agent"

    @abstractmethod
    def run(self, payload: TIn) -> AgentResult[TOut]:
        ...

    def _log_step(self, step: str, detail: str = "") -> None:
        logger.info("[%s] %s %s", self.name, step, detail)
