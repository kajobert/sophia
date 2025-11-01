import json
import os
import pandas as pd
from typing import List, Dict, Any

BENCHMARK_DIR = "docs/benchmarks"
REPORT_FILE = "docs/benchmarks/initial_model_benchmark_report.md"
PRICING_FILE = "docs/openrouter_models.md"

def load_pricing_data() -> pd.DataFrame:
    """Loads model pricing data from the generated Markdown file."""
    records = []
    with open(PRICING_FILE, "r") as f:
        lines = f.readlines()

    for line in lines[2:]: # Skip header and separator
        if not line.startswith("|"):
            continue
        parts = [p.strip() for p in line.split("|") if p.strip()]
        if len(parts) == 5 and "---" not in parts[0]:
            try:
                records.append({
                    "Model": parts[0],
                    "cost_prompt_usd_per_1m": float(parts[3]),
                    "cost_completion_usd_per_1m": float(parts[4]),
                })
            except (ValueError, IndexError):
                continue
    return pd.DataFrame(records)

def load_benchmark_results() -> List[Dict[str, Any]]:
    """Loads all benchmark JSON results from the directory."""
    results = []
    for filename in os.listdir(BENCHMARK_DIR):
        if filename.endswith(".json") and not "error" in filename:
            filepath = os.path.join(BENCHMARK_DIR, filename)
            with open(filepath, "r") as f:
                results.append(json.load(f))
    return results

def calculate_price_performance(results: List[Dict[str, Any]], pricing_df: pd.DataFrame) -> pd.DataFrame:
    """Calculates price/performance metrics and returns a DataFrame."""
    records = []
    for r in results:
        if "error" in r or "quality" not in r or "overall_score" not in r["quality"]:
            continue

        records.append({
            "Model": r["model_name"],
            "Time (s)": r["performance"]["response_time_seconds"],
            "Overall Score": r["quality"]["overall_score"],
            "input_tokens": r["performance"]["input_tokens"],
            "output_tokens": r["performance"]["output_tokens"],
        })

    benchmark_df = pd.DataFrame(records)
    benchmark_df = benchmark_df.drop_duplicates(subset=["Model"])
    merged_df = pd.merge(benchmark_df, pricing_df, on="Model", how="inner")

    # Calculate the cost for each run
    merged_df["Cost (USD)"] = ((merged_df["input_tokens"] / 1_000_000) * merged_df["cost_prompt_usd_per_1m"].astype(float)) + \
                               ((merged_df["output_tokens"] / 1_000_000) * merged_df["cost_completion_usd_per_1m"].astype(float))

    # Calculate Price/Performance score
    # We add a small epsilon to the cost to avoid division by zero for free models.
    merged_df["Price/Performance"] = (merged_df["Overall Score"] * 1000) / (merged_df["Cost (USD)"] + 1e-9)

    return merged_df

def generate_leaderboard(df: pd.DataFrame, title: str, cost_limit_lower: float, cost_limit_upper: float) -> str:
    """Generates a Markdown leaderboard for a specific cost category."""
    df_filtered = df[(df["cost_prompt_usd_per_1m"] > cost_limit_lower) & (df["cost_prompt_usd_per_1m"] <= cost_limit_upper)]
    df_sorted = df_filtered.sort_values(by="Price/Performance", ascending=False)

    report_df = df_sorted[["Model", "cost_prompt_usd_per_1m", "Time (s)", "Overall Score", "Price/Performance"]]
    report_df = report_df.rename(columns={"cost_prompt_usd_per_1m": "Cost (USD/1M Tokens)"})
    report_df["Price/Performance"] = report_df["Price/Performance"].map('{:,.0f}'.format)


    report = f"### {title}\\n\\n"
    report += report_df.to_markdown(index=False)
    report += "\\n\\n"
    return report

def main():
    """Main function to generate the final benchmark report."""
    results = load_benchmark_results()
    pricing_df = load_pricing_data()
    df = calculate_price_performance(results, pricing_df)

    with open(REPORT_FILE, "w") as f:
        f.write("# Initial Model Benchmark Report\\n\\n")
        f.write("This report summarizes the price/performance of various LLM models based on the standard 8-step benchmark.\\n\\n")

        # Leaderboards
        f.write("## Leaderboards by Price Category\\n\\n")
        f.write(generate_leaderboard(df, "Under $0.10/1M Tokens", 0.0, 0.1))
        f.write(generate_leaderboard(df, "$0.10 - $0.20/1M Tokens", 0.1, 0.2))
        f.write(generate_leaderboard(df, "$0.20 - $0.30/1M Tokens", 0.2, 0.3))
        f.write(generate_leaderboard(df, "$0.30 - $0.40/1M Tokens", 0.3, 0.4))
        f.write(generate_leaderboard(df, "$0.40 - $0.50/1M Tokens", 0.4, 0.5))

        # Reference Models
        f.write("## Reference Models ($0.50 - $2.00/1M Tokens)\\n\\n")
        f.write(generate_leaderboard(df, "Reference Models", 0.5, 2.0))

    print(f"Successfully generated benchmark report at {REPORT_FILE}")

if __name__ == "__main__":
    main()
