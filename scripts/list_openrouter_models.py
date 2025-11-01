import os
from typing import List, Dict, Any, Optional
import requests
import pandas as pd
from dotenv import load_dotenv

def fetch_openrouter_models() -> Optional[List[Dict[str, Any]]]:
    """Fetches the list of models and their pricing from the OpenRouter API."""
    try:
        response = requests.get("https://openrouter.ai/api/v1/models")
        response.raise_for_status()
        return response.json()["data"]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from OpenRouter API: {e}")
        return None

def format_as_markdown(models_data: List[Dict[str, Any]]) -> str:
    """Formats the model data into a Markdown table."""
    if not models_data:
        return "No model data to format."

    # Create a pandas DataFrame for easier manipulation and sorting
    df = pd.DataFrame(models_data)

    # Select and rename columns for clarity
    df = df[["id", "name", "pricing", "context_length"]]
    df["cost_prompt_usd_per_1m"] = df["pricing"].apply(lambda x: float(x.get("prompt", 0)) * 1_000_000)
    df["cost_completion_usd_per_1m"] = df["pricing"].apply(lambda x: float(x.get("completion", 0)) * 1_000_000)

    # Select final columns for the report
    df_report = df[[
        "id",
        "name",
        "context_length",
        "cost_prompt_usd_per_1m",
        "cost_completion_usd_per_1m"
    ]]

    # Sort by prompt cost
    df_report = df_report.sort_values(by="cost_prompt_usd_per_1m", ascending=True)

    return df_report.to_markdown(index=False)

def main():
    """Main function to fetch, format, and save the model list."""
    load_dotenv()

    # Check for API key (though not strictly needed for this public endpoint)
    if not os.getenv("OPENROUTER_API_KEY"):
        print("Warning: OPENROUTER_API_KEY is not set in the .env file.")

    print("Fetching model data from OpenRouter...")
    models_data = fetch_openrouter_models()

    if models_data:
        print("Formatting data as Markdown...")
        markdown_table = format_as_markdown(models_data)

        output_path = "docs/openrouter_models.md"
        print(f"Saving model list to {output_path}...")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write("# OpenRouter Model Pricing\n\n")
            f.write("A list of all available models on OpenRouter and their pricing, sorted by prompt cost.\n\n")
            f.write(markdown_table)
        print("Successfully created the model list.")

if __name__ == "__main__":
    main()
