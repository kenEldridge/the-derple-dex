#!/usr/bin/env python3
"""
Convert cdata sources to JSON for Astro static site.

This script uses the cdata library via the bridge pattern to fetch data
programmatically, then transforms it to JSON format for the static site.

Run before astro build: python scripts/prepare-data.py
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Paths (define early for .env loading)
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
OUTPUT_PUBLIC = PROJECT_DIR / "public" / "data"
OUTPUT_SRC = PROJECT_DIR / "src" / "data"

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Explicitly load from project root (handles WSL path issues)
    env_file = PROJECT_DIR / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    else:
        load_dotenv()  # Try default search
except ImportError:
    print("Warning: python-dotenv not installed. Environment variables from .env won't be loaded.")
    print("Install with: pip install python-dotenv")

# Import bridge and dataset configuration
from cdata_bridge import fetch_dataset
from dataset_config import DATASETS

# Dataset type mapping (for processing)
OHLCV_DATASETS = {
    "us_indices", "global_indices", "treasury_yields", "bond_etfs",
    "currencies", "commodities", "sector_etfs", "macro_proxies"
}
RSS_DATASETS = {"fed_news", "financial_news", "economics_news"}
FRED_DATASETS = {
    "fred_gdp", "fred_employment", "fred_inflation", "fred_rates",
    "fred_money", "fred_housing", "fred_consumer", "fred_banking",
    "fred_stress_index", "fred_mev", "fred_market"
}
BLS_DATASETS = {
    "bls_cpi", "bls_employment", "bls_wages", "bls_ppi", "bls_jolts"
}


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

    # Update meta with symbols
    meta = meta.copy()
    meta["symbols"] = symbols

    return {
        "name": name,
        "type": "ohlcv",
        "description": DATASETS[name]["description"],
        "meta": meta,
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


def prepare_fred_dataset(name: str, df: pd.DataFrame, meta: dict, data_type: str = "fred") -> dict:
    """Process FRED/BLS economic datasets (same structure)."""
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

    # Update meta with series
    meta = meta.copy()
    meta["series"] = series_ids

    return {
        "name": name,
        "type": data_type,
        "description": DATASETS[name]["description"],
        "meta": meta,
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

    # Update meta with feeds
    meta = meta.copy()
    meta["feeds"] = feeds

    return {
        "name": name,
        "type": "rss",
        "description": DATASETS[name]["description"],
        "meta": meta,
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
    print("Preparing data for the-derple-dex using cdata bridge...")
    print()

    # Ensure output directories exist
    OUTPUT_PUBLIC.mkdir(parents=True, exist_ok=True)
    OUTPUT_SRC.mkdir(parents=True, exist_ok=True)

    all_datasets = []
    errors = []

    for dataset_name, dataset_config in DATASETS.items():
        print(f"  Fetching {dataset_name}...")

        try:
            # Fetch data using bridge
            df, meta = fetch_dataset(dataset_name, dataset_config)

            if df.empty:
                print(f"    ⚠️  No data returned for {dataset_name}")
                if meta.get("error"):
                    print(f"    Error: {meta['error']}")
                    errors.append(f"{dataset_name}: {meta['error']}")
                continue

            print(f"    Fetched {len(df)} records")

            # Process based on type
            if dataset_name in OHLCV_DATASETS:
                dataset = prepare_ohlcv_dataset(dataset_name, df, meta)
            elif dataset_name in RSS_DATASETS:
                dataset = prepare_rss_dataset(dataset_name, df, meta)
            elif dataset_name in FRED_DATASETS:
                dataset = prepare_fred_dataset(dataset_name, df, meta, data_type="fred")
            elif dataset_name in BLS_DATASETS:
                dataset = prepare_fred_dataset(dataset_name, df, meta, data_type="bls")
            else:
                print(f"    ⚠️  Unknown dataset type for {dataset_name}, skipping")
                continue

            # Write individual dataset JSON for client-side charts
            output_file = OUTPUT_PUBLIC / f"{dataset_name}.json"
            with open(output_file, 'w') as f:
                json.dump(dataset, f, default=str)
            print(f"    → {output_file}")

            # Add summary for datasets.json (without full data)
            summary = {
                "name": dataset["name"],
                "type": dataset["type"],
                "description": dataset["description"],
                "meta": dataset["meta"],
                "stats": dataset["stats"],
            }
            all_datasets.append(summary)

        except Exception as e:
            print(f"    ✗ Error processing {dataset_name}: {e}")
            import traceback
            traceback.print_exc()
            errors.append(f"{dataset_name}: {str(e)}")
            continue

    # Write datasets.json for static page generation
    datasets_file = OUTPUT_SRC / "datasets.json"
    with open(datasets_file, 'w') as f:
        json.dump(all_datasets, f, indent=2, default=str)
    print()
    print(f"  → {datasets_file}")

    print()
    print(f"Done! Processed {len(all_datasets)}/{len(DATASETS)} datasets.")

    if errors:
        print()
        print("Errors encountered:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
