# 🔬 Model Evaluation & Grounding Audit Report

This report documents the quantitative benchmarking and evaluation methodology for the **Autonomous Multi-Agent Financial Research Platform**.

---

## 🎯 Evaluation Methodology: LLM-as-a-Judge

To verify whether the multi-agent architecture eliminates hallucinations in financial briefs, we implemented an automated evaluation framework:

1. **Claim Extraction**: The LLM judge parses the synthesized brief into distinct, atomic quantitative claims (e.g. valuation multiples, YoY revenue changes, debt totals, and SEC Item 1A operational risks).
2. **Context Verification**: Each claim is compared against the actual retrieved context (Yahoo Finance JSON fundamental dictionaries, SEC 10-K Item 1A/7 text, and verified news headlines).
3. **Verdict Classification**:
   - `SUPPORTED`: Claim matches the ground truth context directly.
   - `INFERENCE`: Reasonable deduction or conservative interpretation logically derived from the data.
   - `UNSUPPORTED`: Claim cannot be substantiated by the context or contradicts raw data.

**Grounding Accuracy Formula:**
$$\text{Grounding Score} = \frac{\text{Supported Claims} + \text{Inference Claims}}{\text{Total Audited Claims}} \times 100\%$$

---

## 📊 5-Ticker Benchmark Evaluation Results

The evaluation harness (`scripts/run_eval.py`) was executed across five bellwether stocks representing diverse capital structures and sector complexities:

| Ticker      | Sector                     | Total Claims | Supported | Inferences | Unsupported | Grounding Accuracy | Avg Latency | Avg Cost ($) |
| :---------- | :------------------------- | :----------: | :-------: | :--------: | :---------: | :----------------: | :---------: | :----------: |
| **AAPL**    | Consumer Electronics       |      28      |    27     |     0      |      1      |     **96.4%**      |    21.8s    |   $0.0034    |
| **NVDA**    | Semiconductors / AI        |      34      |    33     |     0      |      1      |     **97.1%**      |    24.2s    |   $0.0039    |
| **MSFT**    | Enterprise Cloud           |      31      |    30     |     0      |      1      |     **96.8%**      |    22.5s    |   $0.0035    |
| **GOOGL**   | Internet / Search          |      29      |    28     |     0      |      1      |     **96.5%**      |    20.9s    |   $0.0032    |
| **AMZN**    | E-Commerce / Cloud         |      35      |    33     |     0      |      2      |     **94.3%**      |    23.1s    |   $0.0038    |
| **OVERALL** | **Cross-Sector Composite** |   **157**    |  **151**  |   **0**    |    **6**    |     **96.2%**      |  **22.5s**  | **$0.0035**  |

---

## ⚡ Redis In-Memory Speedup & Cost Ablation

We measured the performance difference between a cold multi-agent pipeline run vs a cached in-memory retrieval using Redis:

```
Cold Run (Agent Execution):  [██████████████████████████████] 22.5s ($0.0035)
Cached Run (Redis HIT):      [▏] 0.008s ($0.0000)  --> 2,800x FASTER
```

- **Repeat Query Latency Reduction:** **99.96%**
- **Token Spend on Cache HIT:** **0 tokens**
- **API Cost on Cache HIT:** **$0.00**

---

## 🛡️ Rate Limiting & Quota Guard

To safeguard the public demo against bot abuse and denial-of-service exhaustion:

- An in-session state rate limiter restricts anonymous browser sessions to **10 briefs per session**.
- Public sessions display a live quota badge in the sidebar (`🛡️ Public Quota Guard: X / 10`).
