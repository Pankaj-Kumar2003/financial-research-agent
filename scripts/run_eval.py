import os
import sys
import json
import time

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.pipeline import run_multi_agent_pipeline
from agent.evaluation.judge import GroundingJudge
from agent.observability.tracker import ObservabilityTracker

DEFAULT_TICKERS = ["AAPL", "NVDA", "MSFT", "GOOGL", "AMZN"]

def run_benchmark(tickers=None):
    if not tickers:
        tickers = DEFAULT_TICKERS

    print("=" * 65)
    print("      🚀 STARTING INSTITUTIONAL GROUNDING BENCHMARK EVAL")
    print(f"      Tickers: {', '.join(tickers)}")
    print("=" * 65)

    judge = GroundingJudge()
    results = []

    for ticker in tickers:
        print(f"\n[*] Evaluating Ticker: {ticker}...")
        start_time = time.time()

        try:
            with ObservabilityTracker(ticker) as tracker:
                state = run_multi_agent_pipeline(ticker)
                telemetry = tracker.to_dict()

            print(f"    -> Multi-agent execution finished in {telemetry['total_latency_seconds']:.2f}s")
            print(f"    -> Auditing claims with GroundingJudge...")

            eval_result = judge.evaluate(state.final_report, state.raw_data)
            grounding_score = eval_result.get("grounding_score_percent", 100.0)
            claims = eval_result.get("claims", [])
            supported = eval_result.get("supported_count", 0)
            unsupported = eval_result.get("unsupported_count", 0)

            print(f"    -> Grounding Score: {grounding_score}% ({supported} supported, {unsupported} unsupported)")

            results.append({
                "ticker": ticker,
                "latency_seconds": round(telemetry["total_latency_seconds"], 2),
                "tokens": telemetry["total_tokens"],
                "cost_usd": telemetry["estimated_cost_usd"],
                "total_claims": len(claims),
                "supported": supported,
                "unsupported": unsupported,
                "grounding_score": grounding_score
            })

        except Exception as e:
            print(f"    [!] Error evaluating {ticker}: {e}")
            results.append({
                "ticker": ticker,
                "error": str(e)
            })

    # Summary Table
    print("\n" + "=" * 65)
    print("                     BENCHMARK SUMMARY")
    print("=" * 65)
    print(f"{'Ticker':<8} | {'Latency':<8} | {'Tokens':<8} | {'Cost ($)':<8} | {'Grounding (%)':<12}")
    print("-" * 65)

    avg_grounding = 0
    valid_count = 0
    for r in results:
        if "error" not in r:
            print(f"{r['ticker']:<8} | {r['latency_seconds']:<7}s | {r['tokens']:<8} | ${r['cost_usd']:<7.5f} | {r['grounding_score']:<12}%")
            avg_grounding += r['grounding_score']
            valid_count += 1

    if valid_count > 0:
        print("-" * 65)
        print(f"AVERAGE GROUNDING ACCURACY: {avg_grounding / valid_count:.1f}%")
        print("=" * 65)

    # Save to file
    os.makedirs("reports", exist_ok=True)
    report_file = os.path.join("reports", "benchmark_summary.json")
    with open(report_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[+] Detailed benchmark saved to {report_file}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run Multi-Agent Financial Grounding Benchmark")
    parser.add_argument("--tickers", nargs="+", default=["AAPL", "NVDA"], help="Tickers to benchmark")
    args = parser.parse_args()
    run_benchmark(args.tickers)
