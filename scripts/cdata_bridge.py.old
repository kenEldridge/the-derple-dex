"""
CData Bridge - Uses cdata as a library to fetch data programmatically.

This module implements the "bridge pattern" from cdata issue #4:
https://github.com/kenEldridge/cdata/issues/4

Instead of reading Parquet files from a separate cdata project, this module:
1. Creates SourceConfig objects programmatically
2. Uses cdata's registry to create source instances
3. Fetches data directly and returns DataFrames
4. Owns its own configuration (no dependency on cdata YAML files)
"""

from datetime import datetime
from typing import Any, Optional

import pandas as pd
from cdata.config.schema import SourceConfig
from cdata.core.registry import get_registry


class CDataBridge:
    """Bridge to cdata framework - this project owns config and storage."""

    def __init__(self):
        self._registry = None

    @property
    def registry(self):
        """Lazy load cdata registry."""
        if self._registry is None:
            self._registry = get_registry()
        return self._registry

    def _fetch(
        self,
        source_id: str,
        source_name: str,
        source_type: str,
        config: dict[str, Any],
        primary_keys: list[str]
    ) -> tuple[pd.DataFrame, dict]:
        """
        Generic fetch method using cdata registry.

        Returns:
            tuple: (DataFrame with data, metadata dict)
        """
        started_at = datetime.utcnow()

        # Create SourceConfig programmatically
        source_config = SourceConfig(
            id=source_id,
            name=source_name,
            type=source_type,
            config=config,
            primary_keys=primary_keys
        )

        # Create source instance from registry
        source = self.registry.create_source(source_config)
        if source is None:
            raise ValueError(f"Source type '{source_type}' not found in registry")

        # Fetch data
        result = source.fetch(**config)

        # Convert records to DataFrame
        if result.records:
            df = pd.DataFrame([r.data for r in result.records])
        else:
            df = pd.DataFrame()

        completed_at = datetime.utcnow()

        # Build metadata
        metadata = {
            "record_count": len(df),
            "first_fetched": started_at.isoformat(),
            "last_updated": completed_at.isoformat(),
            "last_record_date": None,
            "fetch_count": 1,
            "columns": list(df.columns) if not df.empty else [],
            "primary_keys": primary_keys,
            "error": result.error if hasattr(result, 'error') else None
        }

        # Try to determine last record date
        if not df.empty:
            if 'date' in df.columns:
                try:
                    last_date = pd.to_datetime(df['date'], utc=True).max()
                    metadata["last_record_date"] = last_date.isoformat()
                except Exception:
                    pass
            elif 'published' in df.columns:
                try:
                    last_pub = pd.to_datetime(df['published'], utc=True).max()
                    metadata["last_record_date"] = last_pub.isoformat()
                except Exception:
                    pass

        return df, metadata

    def fetch_yfinance_data(
        self,
        source_id: str,
        name: str,
        description: str,
        symbols: list[str],
        period: str = "1y",
        interval: str = "1d",
        primary_keys: Optional[list[str]] = None
    ) -> tuple[pd.DataFrame, dict]:
        """
        Fetch Yahoo Finance data.

        Args:
            source_id: Unique identifier for this dataset
            name: Human-readable name
            description: Dataset description
            symbols: List of ticker symbols
            period: Time period (e.g., "1y", "2y", "5y", "max")
            interval: Data interval (e.g., "1d", "1wk", "1mo")
            primary_keys: Primary key columns (default: ["symbol", "date"])

        Returns:
            tuple: (DataFrame, metadata dict)
        """
        if primary_keys is None:
            primary_keys = ["symbol", "date"]

        config = {
            "symbols": symbols,
            "period": period,
            "interval": interval
        }

        return self._fetch(source_id, name, "yfinance", config, primary_keys)

    def fetch_rss_data(
        self,
        source_id: str,
        name: str,
        description: str,
        feeds: list[dict[str, str]],
        primary_keys: Optional[list[str]] = None
    ) -> tuple[pd.DataFrame, dict]:
        """
        Fetch RSS feed data.

        Args:
            source_id: Unique identifier for this dataset
            name: Human-readable name
            description: Dataset description
            feeds: List of feed dicts with 'name' and 'url' keys
            primary_keys: Primary key columns (default: ["id"])

        Returns:
            tuple: (DataFrame, metadata dict)
        """
        if primary_keys is None:
            primary_keys = ["id"]

        config = {
            "feeds": feeds
        }

        return self._fetch(source_id, name, "rss", config, primary_keys)

    def fetch_fred_data(
        self,
        source_id: str,
        name: str,
        description: str,
        series: list[str],
        primary_keys: Optional[list[str]] = None
    ) -> tuple[pd.DataFrame, dict]:
        """
        Fetch FRED economic data.

        Args:
            source_id: Unique identifier for this dataset
            name: Human-readable name
            description: Dataset description
            series: List of FRED series IDs
            primary_keys: Primary key columns (default: ["series_id", "date"])

        Returns:
            tuple: (DataFrame, metadata dict)
        """
        if primary_keys is None:
            primary_keys = ["series_id", "date"]

        config = {
            "series": series
        }

        return self._fetch(source_id, name, "fred", config, primary_keys)

    def fetch_bls_data(
        self,
        source_id: str,
        name: str,
        description: str,
        series: list[str],
        primary_keys: Optional[list[str]] = None
    ) -> tuple[pd.DataFrame, dict]:
        """
        Fetch BLS labor statistics data.

        Args:
            source_id: Unique identifier for this dataset
            name: Human-readable name
            description: Dataset description
            series: List of BLS series IDs
            primary_keys: Primary key columns (default: ["series_id", "date"])

        Returns:
            tuple: (DataFrame, metadata dict)
        """
        if primary_keys is None:
            primary_keys = ["series_id", "date"]

        config = {
            "series": series
        }

        return self._fetch(source_id, name, "bls", config, primary_keys)


# Global bridge instance
_bridge = None


def get_bridge() -> CDataBridge:
    """Get global CDataBridge instance (singleton pattern)."""
    global _bridge
    if _bridge is None:
        _bridge = CDataBridge()
    return _bridge


def fetch_dataset(dataset_id: str, dataset_config: dict) -> tuple[pd.DataFrame, dict]:
    """
    Fetch a dataset using its configuration.

    Args:
        dataset_id: Dataset identifier
        dataset_config: Dataset configuration dict with 'name', 'type', 'description', 'config', 'primary_keys'

    Returns:
        tuple: (DataFrame, metadata dict)
    """
    bridge = get_bridge()

    source_type = dataset_config["type"]
    name = dataset_config["name"]
    description = dataset_config["description"]
    config = dataset_config["config"]
    primary_keys = dataset_config.get("primary_keys", [])

    if source_type == "yfinance":
        return bridge.fetch_yfinance_data(
            dataset_id,
            name,
            description,
            symbols=config["symbols"],
            period=config.get("period", "1y"),
            interval=config.get("interval", "1d"),
            primary_keys=primary_keys
        )
    elif source_type == "rss":
        return bridge.fetch_rss_data(
            dataset_id,
            name,
            description,
            feeds=config["feeds"],
            primary_keys=primary_keys
        )
    elif source_type == "fred":
        return bridge.fetch_fred_data(
            dataset_id,
            name,
            description,
            series=config["series"],
            primary_keys=primary_keys
        )
    elif source_type == "bls":
        return bridge.fetch_bls_data(
            dataset_id,
            name,
            description,
            series=config["series"],
            primary_keys=primary_keys
        )
    else:
        raise ValueError(f"Unsupported source type: {source_type}")
