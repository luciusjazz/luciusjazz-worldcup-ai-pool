from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class AgentResult:
    findings: list[str] = field(default_factory=list)
    confidence: float = 0.5
    recommendations: list[str] = field(default_factory=list)


class BaseAgent(ABC):
    name: str = "BaseAgent"
    weight: float = 0.0

    @abstractmethod
    def analyze(self, context: dict) -> AgentResult:
        """Analisa o contexto e retorna findings, confidence e recommendations."""
