#!/usr/bin/env python3
"""
Convert cdata parquet files to JSON for Astro static site.
Run before astro build: python scripts/prepare-data.py
"""
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Paths - adjust if needed
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
CDATA_PATH = PROJECT_DIR.parent / "cdata" / "data"
OUTPUT_PUBLIC = PROJECT_DIR / "public" / "data"
OUTPUT_SRC = PROJECT_DIR / "src" / "data"

# Dataset type mapping
OHLCV_DATASETS = {
    "us_indices", "global_indices", "treasury_yields", "bond_etfs",
    "currencies", "commodities", "sector_etfs", "macro_proxies"
}
RSS_DATASETS = {"fed_news", "financial_news", "economics_news"}
FRED_DATASETS = {
    "fred_gdp", "fred_employment", "fred_inflation", "fred_rates",
    "fred_money", "fred_housing", "fred_consumer"
}


def load_index() -> dict:
    """Load cdata index.json."""
    index_path = CDATA_PATH / "index.json"
    if not index_path.exists():
        print(f"Error: Index not found at {index_path}")
        sys.exit(1)
    with open(index_path) as f:
        return json.load(f)


def prepare_ohlcv_dataset(name: str, df: pd.DataFrame, meta: dict) -> dict:
    """Process OHLCV (price) datasets."""
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'], utc=True)

    # Get unique symbols
    symbols = sorted(df['symbol'].unique().tolist())

    # Compute stats per symbol
    symbol_stats = {}
    for symbol in symbols:
        sdf = df[df['symbol'] == symbol]
        symbol_stats[symbol] = {
            "count": len(sdf),
            "date_min": sdf['date'].min().isoformat(),
            "date_max": sdf['date'].max().isoformat(),
            "close_mean": round(float(sdf['close'].mean()), 4),
            "close_min": round(float(sdf['close'].min()), 4),
            "close_max": round(float(sdf['close'].max()), 4),
            "close_std": round(float(sdf['close'].std()), 4) if len(sdf) > 1 else 0,
            "volume_total": int(sdf['volume'].sum()),
        }

    # Overall date range
    date_min = df['date'].min()
    date_max = df['date'].max()

    # Sample data for charts (all data, sorted)
    sample_df = df.sort_values(['symbol', 'date'])[['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']]
    sample_df['date'] = sample_df['date'].dt.strftime('%Y-%m-%d')

    return {
        "name": name,
        "type": "ohlcv",
        "description": meta.get("description", ""),
        "meta": {
            "record_count": int(meta.get("record_count", len(df))),
            "first_fetched": meta.get("first_fetched"),
            "last_updated": meta.get("last_updated"),
            "last_record_date": meta.get("last_record_date"),
            "fetch_count": int(meta.get("fetch_count", 1)),
            "columns": meta.get("columns", list(df.columns)),
            "primary_keys": meta.get("primary_keys", []),
            "symbols": symbols,
        },
        "stats": {
            "date_range": {
                "min": date_min.isoformat(),
                "max": date_max.isoformat(),
                "days": (date_max - date_min).days,
            },
            "by_symbol": symbol_stats,
        },
        "data": sample_df.to_dict(orient='records'),
    }


def prepare_fred_dataset(name: str, df: pd.DataFrame, meta: dict) -> dict:
    """Process FRED economic datasets."""
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'], utc=True)

    # Get unique series
    series_ids = sorted(df['series_id'].unique().tolist())

    # Compute stats per series
    series_stats = {}
    for series_id in series_ids:
        sdf = df[df['series_id'] == series_id]
        title = sdf['title'].iloc[0] if 'title' in sdf.columns and len(sdf) > 0 else series_id
        units = sdf['units'].iloc[0] if 'units' in sdf.columns and len(sdf) > 0 else ""
        frequency = sdf['frequency'].iloc[0] if 'frequency' in sdf.columns and len(sdf) > 0 else ""
        series_stats[series_id] = {
            "title": title,
            "units": units,
            "frequency": frequency,
            "count": len(sdf),
            "date_min": sdf['date'].min().isoformat(),
            "date_max": sdf['date'].max().isoformat(),
            "value_mean": round(float(sdf['value'].mean()), 4),
            "value_min": round(float(sdf['value'].min()), 4),
            "value_max": round(float(sdf['value'].max()), 4),
            "value_latest": round(float(sdf.sort_values('date').iloc[-1]['value']), 4),
        }

    # Overall date range
    date_min = df['date'].min()
    date_max = df['date'].max()

    # Data for charts (all data, sorted)
    sample_df = df.sort_values(['series_id', 'date'])[['series_id', 'date', 'value', 'title', 'units']]
    sample_df['date'] = sample_df['date'].dt.strftime('%Y-%m-%d')

    return {
        "name": name,
        "type": "fred",
        "description": meta.get("description", ""),
        "meta": {
            "record_count": int(meta.get("record_count", len(df))),
            "first_fetched": meta.get("first_fetched"),
            "last_updated": meta.get("last_updated"),
            "last_record_date": meta.get("last_record_date"),
            "fetch_count": int(meta.get("fetch_count", 1)),
            "columns": meta.get("columns", list(df.columns)),
            "primary_keys": meta.get("primary_keys", []),
            "series": series_ids,
        },
        "stats": {
            "date_range": {
                "min": date_min.isoformat(),
                "max": date_max.isoformat(),
                "days": (date_max - date_min).days,
            },
            "by_series": series_stats,
        },
        "data": sample_df.to_dict(orient='records'),
    }


def prepare_rss_dataset(name: str, df: pd.DataFrame, meta: dict) -> dict:
    """Process RSS news datasets."""
    df = df.copy()

    # Handle published date
    if 'published' in df.columns:
        df['published'] = pd.to_datetime(df['published'], utc=True, errors='coerce')
        df = df.dropna(subset=['published'])

    # Get feeds
    feeds = []
    if 'feed_name' in df.columns:
        feeds = sorted(df['feed_name'].unique().tolist())

    # Articles by feed
    articles_by_feed = {}
    if 'feed_name' in df.columns:
        articles_by_feed = df.groupby('feed_name').size().to_dict()

    # Date range
    date_min = df['published'].min() if len(df) > 0 else None
    date_max = df['published'].max() if len(df) > 0 else None

    # Articles by day (for histogram)
    articles_by_day = {}
    if len(df) > 0:
        daily = df.groupby(df['published'].dt.date).size()
        articles_by_day = {str(k): int(v) for k, v in daily.items()}

    # Recent articles (last 30)
    recent_cols = ['title', 'link', 'published', 'feed_name', 'author']
    available_cols = [c for c in recent_cols if c in df.columns]
    recent_df = df.sort_values('published', ascending=False).head(30)[available_cols].copy()
    if 'published' in recent_df.columns:
        recent_df['published'] = recent_df['published'].dt.strftime('%Y-%m-%d %H:%M')

    return {
        "name": name,
        "type": "rss",
        "description": meta.get("description", ""),
        "meta": {
            "record_count": int(meta.get("record_count", len(df))),
            "first_fetched": meta.get("first_fetched"),
            "last_updated": meta.get("last_updated"),
            "last_record_date": meta.get("last_record_date"),
            "fetch_count": int(meta.get("fetch_count", 1)),
            "columns": meta.get("columns", list(df.columns)),
            "primary_keys": meta.get("primary_keys", []),
            "feeds": feeds,
        },
        "stats": {
            "date_range": {
                "min": date_min.isoformat() if date_min else None,
                "max": date_max.isoformat() if date_max else None,
                "days": (date_max - date_min).days if date_min and date_max else 0,
            },
            "articles_by_feed": articles_by_feed,
            "articles_by_day": articles_by_day,
        },
        "data": recent_df.to_dict(orient='records'),
    }


def main():
    print("Preparing data for the-derple-dex...")

    # Ensure output directories exist
    OUTPUT_PUBLIC.mkdir(parents=True, exist_ok=True)
    OUTPUT_SRC.mkdir(parents=True, exist_ok=True)

    # Load index
    index = load_index()
    datasets_info = index.get("datasets", {})

    all_datasets = []

    for key, meta in datasets_info.items():
        name = meta.get("name")
        file_path = CDATA_PATH.parent / meta.get("file_path", "")

        if not file_path.exists():
            print(f"  Skipping {name}: file not found at {file_path}")
            continue

        print(f"  Processing {name}...")

        # Read parquet
        df = pd.read_parquet(file_path)

        # Process based on type
        if name in OHLCV_DATASETS:
            dataset = prepare_ohlcv_dataset(name, df, meta)
        elif name in RSS_DATASETS:
            dataset = prepare_rss_dataset(name, df, meta)
        elif name in FRED_DATASETS:
            dataset = prepare_fred_dataset(name, df, meta)
        else:
            print(f"  Unknown dataset type for {name}, skipping")
            continue

        # Write individual dataset JSON for client-side charts
        output_file = OUTPUT_PUBLIC / f"{name}.json"
        with open(output_file, 'w') as f:
            json.dump(dataset, f, default=str)
        print(f"    -> {output_file}")

        # Add summary for datasets.json (without full data)
        summary = {
            "name": dataset["name"],
            "type": dataset["type"],
            "description": dataset["description"],
            "meta": dataset["meta"],
            "stats": dataset["stats"],
        }
        all_datasets.append(summary)

    # Write datasets.json for static page generation
    datasets_file = OUTPUT_SRC / "datasets.json"
    with open(datasets_file, 'w') as f:
        json.dump(all_datasets, f, indent=2, default=str)
    print(f"  -> {datasets_file}")

    print(f"\nDone! Processed {len(all_datasets)} datasets.")


if __name__ == "__main__":
    main()
