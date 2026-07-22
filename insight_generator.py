"""
insight_generator.py
Combines quantitative analysis (from pandas) with qualitative summaries
(from text documents) and asks the LLM to produce a narrative analysis:
what happened, why it likely happened, and what to watch next.
"""
import os
import json
import anthropic

MODEL = "claude-sonnet-4-5"


def get_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "Set the ANTHROPIC_API_KEY environment variable before running this module."
        )
    return anthropic.Anthropic(api_key=api_key)


def generate_insights(stats_summary: dict, anomalies: str, text_summary: str) -> str:
    """
    Produce a narrative report section that ties numeric trends/anomalies
    to qualitative context pulled from documents.
    """
    client = get_client()

    prompt = f"""You are a business analyst writing the "Insights & Analysis" section
of an internal report. You have three inputs:

1. GROUPED NUMERIC SUMMARY (sums/means/counts by category):
{json.dumps(stats_summary, indent=2, default=str)}

2. DETECTED ANOMALIES (statistical outliers in the data):
{anomalies}

3. QUALITATIVE CONTEXT (summarized notes from internal documents):
{text_summary}

Write 3-5 short paragraphs that:
- Identify the most important patterns or anomalies in the numbers
- Explain likely causes, but ONLY if supported by the qualitative context —
  otherwise say the cause is unclear and worth investigating
- End with 2-3 concrete recommended next steps

Be direct and concise. Do not restate raw numbers verbatim, interpret them.
"""
    response = client.messages.create(
        model=MODEL,
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


if __name__ == "__main__":
    dummy_stats = {"region": {"North": 22050, "East": 18680}}
    dummy_anomalies = "North region Widget A units_sold dropped to 30 in June (z=-2.1)"
    dummy_text_summary = "- North supplier shortage in June delayed restocking"
    print(generate_insights(dummy_stats, dummy_anomalies, dummy_text_summary))
