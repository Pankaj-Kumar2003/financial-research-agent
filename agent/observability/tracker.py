import time
from typing import Dict, Any

class ObservabilityTracker:
    """
    Observability tracker context manager measuring wall-clock latencies,
    token counts, and estimated USD costs across agent operations.
    """
    
    # Cost estimations per 1,000 tokens (Groq / OpenRouter average)
    COST_PER_1K_TOKENS = 0.0002
    
    def __init__(self, ticker: str):
        self.ticker = ticker.upper()
        self.start_time = 0.0
        self.end_time = 0.0
        self.llm_latency = 0.0
        self.tool_latency = 0.0
        self.total_tokens = 0
        self.estimated_cost = 0.0
        self.error_count = 0
        self.tool_calls = 0
        self.retrieved_documents = 0
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        if exc_type is not None:
            self.error_count += 1

    @property
    def total_latency(self) -> float:
        if self.end_time > 0:
            return round(self.end_time - self.start_time, 3)
        return round(time.time() - self.start_time, 3)

    def log_llm_call(self, prompt: str, response: str, latency: float):
        """Calculates token counts and costs from LLM text length."""
        self.llm_latency += latency
        # Simple word-count multiplier estimation (~1.3 tokens per word)
        input_words = len(prompt.split())
        output_words = len(response.split())
        est_tokens = int((input_words + output_words) * 1.3)
        
        self.total_tokens += est_tokens
        self.estimated_cost += (est_tokens / 1000.0) * self.COST_PER_1K_TOKENS

    def log_tool_call(self, tool_name: str, latency: float, docs_retrieved: int = 1, success: bool = True):
        """Logs tool execution telemetry."""
        self.tool_latency += latency
        self.tool_calls += 1
        self.retrieved_documents += docs_retrieved
        if not success:
            self.error_count += 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticker": self.ticker,
            "total_latency_seconds": self.total_latency,
            "llm_latency_seconds": round(self.llm_latency, 3),
            "tool_latency_seconds": round(self.tool_latency, 3),
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": round(self.estimated_cost, 6),
            "error_count": self.error_count,
            "tool_calls": self.tool_calls,
            "retrieved_documents": self.retrieved_documents
        }
