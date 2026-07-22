"""
api_ingestor.py
Fetches live data from a JSON API endpoint and normalizes it into a DataFrame.
"""
import requests
import pandas as pd


def fetch_api_data(url: str, record_path: str = None, params: dict = None) -> pd.DataFrame:
    """
    Fetch JSON from an API and flatten it into a DataFrame.

    record_path: dotted key path to the list of records if nested,
                 e.g. "data.results". Leave None if the response is
                 already a flat list of records.
    """
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    payload = resp.json()

    if record_path:
        for key in record_path.split("."):
            payload = payload[key]

    df = pd.json_normalize(payload)
    return df


if __name__ == "__main__":
    # Demo against a free public API
    df = fetch_api_data("https://api.exchangerate-api.com/v4/latest/USD")
    print(df.head())
