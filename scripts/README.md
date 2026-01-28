# Data Preparation Scripts

## Current Implementation

**`prepare-data-v2.py`** - Reads from cdata's local Parquet storage

This script:
- Reads from `data/raw/*.parquet` files managed by cdata
- Transforms Parquet data to JSON format
- Outputs to `public/data/*.json` for client-side charts
- Outputs to `src/data/datasets.json` for static site generation

**Usage:**
```bash
# Fetch latest data
python3 -m cdata fetch all

# Convert to JSON
python3 scripts/prepare-data-v2.py

# Or use npm script (runs both)
npm run build
```

## Architecture

```
cdata (local instance in this project)
  ↓ Fetches from APIs
  ↓ Stores in data/raw/*.parquet
  ↓
prepare-data-v2.py
  ↓ Reads Parquet files
  ↓ Transforms to JSON
  ↓
Astro build
  ↓ Static site generation
```

## Historical Files (`.old` suffix)

These files represent a previous approach that bypassed cdata's storage management:

- **`cdata_bridge.py.old`** - Custom bridge that fetched directly via cdata registry
- **`dataset_config.py.old`** - Python-based dataset configurations
- **`prepare-data.py.old`** - Used the bridge to fetch fresh data on every build

**Why changed:** The old approach defeated the purpose of cdata's incremental storage. The current approach uses cdata as intended: as a local data management system with Parquet storage and incremental updates.

**Reference:** See [cdata issue #4](https://github.com/kenEldridge/cdata/issues/4) for the bridge pattern discussion.

Kept as `.old` files for reference in case we need to understand the evolution of the architecture.
