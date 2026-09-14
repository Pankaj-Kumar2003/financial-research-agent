from abc import ABC, abstractmethod
from agent.core.state import ResearchState

class BaseAgent(ABC):
    """
    Abstract Base Class for all autonomous agents in the pipeline.
    Enforces a standardized execution interface.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the agent (e.g. 'DataGatherer')"""
        pass
        
    @property
    @abstractmethod
    def role(self) -> str:
        """A brief description of what this agent does."""
        pass

    @abstractmethod
    def run(self, state: ResearchState) -> ResearchState:
        """
        Execute the agent's logic.
        Reads necessary data from `state`, performs processing/LLM calls,
        and returns an updated `ResearchState`.
        """
        pass

