#!/usr/bin/env python3
"""
Convert cdata fetched data to JSON for Astro static site (Bridge Pattern).

This script uses cdata as a library via the bridge pattern. Instead of reading
Parquet files, it:
1. Fetches data programmatically using the cdata registry
2. Transforms to JSON format for the static site
3. Owns its own dataset configuration

Run: python scripts/prepare-data-v3.py

To set API keys: export FRED_API_KEY="your_key"
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

# Import our bridge and config modules
from dataset_config import DATASETS, OHLCV_DATASETS, RSS_DATASETS, FRED_DATASETS, BLS_DATASETS, FED_STRESS_DATASETS
from cdata_bridge import get_bridge

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
OUTPUT_PUBLIC = PROJECT_DIR / "public" / "data"
OUTPUT_SRC = PROJECT_DIR / "src" / "data"

# Load environment variables
load_dotenv(PROJECT_DIR / ".env")

# Check if restricted data should be included (Yahoo Finance - Personal/Research Use)
# Default to True for local development, set to False for public deployments
INCLUDE_RESTRICTED_DATA = os.getenv("INCLUDE_RESTRICTED_DATA", "true").lower() in ("true", "1", "yes")


def prepare_ohlcv_dataset(name: str, df: pd.DataFrame, config: dict) -> dict:
    """Process OHLCV (price) datasets."""
    df = df.copy()

    # Remove cdata internal columns
    df = df[[c for c in df.columns if not c.startswith('_')]]

    # Handle empty DataFrame
    if len(df) == 0 or 'date' not in df.columns or 'symbol' not in df.columns:
        return {
            "name": name,
            "type": "ohlcv",
            "description": config.get("description", ""),
            "meta": {
                "name": name,
                "source_id": name,
                "location": "bridge",
                "format": "dataframe",
                "record_count": 0,
                "columns": list(df.columns) if len(df.columns) > 0 else [],
                "primary_keys": config.get("primary_keys", []),
                "fetched_at": datetime.utcnow().isoformat(),
                "description": config.get("description", ""),
                "symbols": [],
            },
            "stats": {
                "date_range": {
                    "min": None,
                    "max": None,
                    "days": 0,
                },
                "by_symbol": {},
            },
            "data": [],
        }

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

    # Create metadata
    meta = {
        "name": name,
        "source_id": name,
        "location": "bridge",
        "format": "dataframe",
        "record_count": len(df),
        "columns": list(df.columns),
        "primary_keys": config.get("primary_keys", []),
        "fetched_at": datetime.utcnow().isoformat(),
        "description": config.get("description", ""),
        "symbols": symbols,
    }

    return {
        "name": name,
        "type": "ohlcv",
        "description": config.get("description", ""),
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


def prepare_fred_dataset(name: str, df: pd.DataFrame, config: dict, data_type: str = "fred") -> dict:
    """Process FRED/BLS economic datasets (same structure)."""
    df = df.copy()

    # Remove cdata internal columns
    df = df[[c for c in df.columns if not c.startswith('_')]]

    # Handle empty DataFrame
    if len(df) == 0 or 'date' not in df.columns or 'series_id' not in df.columns:
        # Return minimal dataset for empty results
        return {
            "name": name,
            "type": data_type,
            "description": config.get("description", ""),
            "meta": {
                "name": name,
                "source_id": name,
                "location": "bridge",
                "format": "dataframe",
                "record_count": 0,
                "columns": list(df.columns) if len(df.columns) > 0 else [],
                "primary_keys": config.get("primary_keys", []),
                "fetched_at": datetime.utcnow().isoformat(),
                "description": config.get("description", ""),
                "series": [],
            },
            "stats": {
                "date_range": {
                    "min": None,
                    "max": None,
                    "days": 0,
                },
                "by_series": {},
            },
            "data": [],
        }

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

    # Create metadata
    meta = {
        "name": name,
        "source_id": name,
        "location": "bridge",
        "format": "dataframe",
        "record_count": len(df),
        "columns": list(df.columns),
        "primary_keys": config.get("primary_keys", []),
        "fetched_at": datetime.utcnow().isoformat(),
        "description": config.get("description", ""),
        "series": series_ids,
    }

    return {
        "name": name,
        "type": data_type,
        "description": config.get("description", ""),
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


def prepare_rss_dataset(name: str, df: pd.DataFrame, config: dict) -> dict:
    """Process RSS news datasets."""
    df = df.copy()

    # Remove cdata internal columns
    df = df[[c for c in df.columns if not c.startswith('_')]]

    # Handle empty DataFrame
    if len(df) == 0:
        return {
            "name": name,
            "type": "rss",
            "description": config.get("description", ""),
            "meta": {
                "name": name,
                "source_id": name,
                "location": "bridge",
                "format": "dataframe",
                "record_count": 0,
                "columns": list(df.columns) if len(df.columns) > 0 else [],
                "primary_keys": config.get("primary_keys", []),
                "fetched_at": datetime.utcnow().isoformat(),
                "description": config.get("description", ""),
                "feeds": [],
            },
            "stats": {
                "date_range": {
                    "min": None,
                    "max": None,
                    "days": 0,
                },
                "articles_by_feed": {},
                "articles_by_day": {},
            },
            "data": [],
        }

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

    # Create metadata
    meta = {
        "name": name,
        "source_id": name,
        "location": "bridge",
        "format": "dataframe",
        "record_count": len(df),
        "columns": list(df.columns),
        "primary_keys": config.get("primary_keys", []),
        "fetched_at": datetime.utcnow().isoformat(),
        "description": config.get("description", ""),
        "feeds": feeds,
    }

    return {
        "name": name,
        "type": "rss",
        "description": config.get("description", ""),
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


def prepare_fed_stress_dataset(name: str, df: pd.DataFrame, config: dict) -> dict:
    """Process Federal Reserve stress test scenario datasets."""
    df = df.copy()

    # Remove cdata internal columns
    df = df[[c for c in df.columns if not c.startswith('_')]]

    # Fed stress data uses quarter format "YYYY Q#" not datetime
    # Keep as string for proper handling

    # Get unique years and scenarios (check if columns exist)
    years = sorted(df['year'].unique().tolist()) if 'year' in df.columns else []
    scenarios = []

    # The scenario info might be in the 'table' column name
    if 'table' in df.columns:
        scenarios = sorted(df['table'].unique().tolist())

    # Get quarters or dates
    if 'date' in df.columns:
        periods = sorted(df['date'].astype(str).unique().tolist())
        period_min = periods[0] if periods else None
        period_max = periods[-1] if periods else None
    else:
        period_min = None
        period_max = None

    # Data for charts (all data, sorted)
    sort_cols = []
    if 'year' in df.columns:
        sort_cols.append('year')
    if 'table' in df.columns:
        sort_cols.append('table')
    if 'date' in df.columns:
        sort_cols.append('date')

    sample_df = df.sort_values(sort_cols) if sort_cols else df

    # Create metadata
    meta = {
        "name": name,
        "source_id": name,
        "location": "bridge",
        "format": "dataframe",
        "record_count": len(df),
        "columns": list(df.columns),
        "primary_keys": config.get("primary_keys", []),
        "fetched_at": datetime.utcnow().isoformat(),
        "description": config.get("description", ""),
        "years": years,
        "scenarios": scenarios,
    }

    return {
        "name": name,
        "type": "fed_stress",
        "description": config.get("description", ""),
        "meta": meta,
        "stats": {
            "date_range": {
                "min": str(period_min) if period_min else None,
                "max": str(period_max) if period_max else None,
                "days": 0,  # Not applicable for quarterly data
            },
            "years": years,
            "scenarios": scenarios,
            "record_count": len(df),
        },
        "data": sample_df.to_dict(orient='records'),
    }


def main():
    print("Preparing data for the-derple-dex using cdata bridge pattern...")
    print()

    # Clean output directories to remove old data files
    import shutil
    if OUTPUT_PUBLIC.exists():
        shutil.rmtree(OUTPUT_PUBLIC)
    if not INCLUDE_RESTRICTED_DATA:
        print("  Note: INCLUDE_RESTRICTED_DATA=false - excluding Yahoo Finance datasets")
        print()

    # Ensure output directories exist
    OUTPUT_PUBLIC.mkdir(parents=True, exist_ok=True)
    OUTPUT_SRC.mkdir(parents=True, exist_ok=True)

    # Get bridge instance
    bridge = get_bridge()

    all_datasets = []
    errors = []

    for name, dataset_config in DATASETS.items():
        source_type = dataset_config["type"]
        description = dataset_config.get("description", "")
        config_params = dataset_config["config"]
        primary_keys = dataset_config.get("primary_keys", [])
        incremental = dataset_config.get("incremental", False)

        # Skip Yahoo Finance datasets in public builds (Personal/Research Use only)
        if not INCLUDE_RESTRICTED_DATA and name in OHLCV_DATASETS:
            print(f"  Skipping {name}: restricted dataset (Yahoo Finance - Personal/Research Use)")
            continue

        print(f"  Fetching {name}...")

        try:
            # Fetch data using bridge
            if source_type == "yfinance":
                df = bridge.fetch_yfinance_data(
                    source_id=name,
                    symbols=config_params["symbols"],
                    period=config_params.get("period", "1y"),
                    interval=config_params.get("interval", "1d")
                )
            elif source_type == "rss":
                df = bridge.fetch_rss_data(
                    source_id=name,
                    feeds=config_params["feeds"]
                )
            elif source_type == "fred":
                df = bridge.fetch_fred_data(
                    source_id=name,
                    series=config_params["series"]
                )
            elif source_type == "bls":
                df = bridge.fetch_bls_data(
                    source_id=name,
                    series=config_params["series"]
                )
            elif source_type == "fed_stress":
                df = bridge.fetch_fed_stress_data(
                    source_id=name,
                    years=config_params["years"],
                    scenarios=config_params["scenarios"]
                )
            else:
                print(f"    Unknown source type: {source_type}, skipping")
                continue

            print(f"    Fetched {len(df)} records")

            # Process based on type
            if name in OHLCV_DATASETS:
                dataset = prepare_ohlcv_dataset(name, df, dataset_config)
            elif name in RSS_DATASETS:
                dataset = prepare_rss_dataset(name, df, dataset_config)
            elif name in FRED_DATASETS:
                dataset = prepare_fred_dataset(name, df, dataset_config, data_type="fred")
            elif name in BLS_DATASETS:
                dataset = prepare_fred_dataset(name, df, dataset_config, data_type="bls")
            elif name in FED_STRESS_DATASETS:
                dataset = prepare_fed_stress_dataset(name, df, dataset_config)
            else:
                print(f"    Unknown dataset category for {name}, skipping")
                continue

            # Write individual dataset JSON for client-side charts
            output_file = OUTPUT_PUBLIC / f"{name}.json"
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
            print(f"    ✗ Error processing {name}: {e}")
            import traceback
            traceback.print_exc()
            errors.append(f"{name}: {str(e)}")
            continue

    # Write datasets.json for static page generation
    datasets_file = OUTPUT_SRC / "datasets.json"
    with open(datasets_file, 'w') as f:
        json.dump(all_datasets, f, indent=2, default=str)
    print()
    print(f"  → {datasets_file}")

    print()
    print(f"Done! Processed {len(all_datasets)} datasets using bridge pattern.")

    if errors:
        print()
        print("Errors encountered:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
