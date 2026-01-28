# the-derple-dex - Project Guide for AI Assistants

This is a technical blog and data showcase site built with Astro. It displays financial and economic data managed by [cdata](https://github.com/kenEldridge/cdata) initialized locally.

## Architecture Overview

**Current Approach:** Local cdata Instance with Parquet Storage

- cdata is initialized **within** this project (not as a separate pipeline)
- Dataset configurations are in `config/sources/financial.yaml`
- Data is stored in `data/raw/*.parquet` files (managed by cdata)
- Incremental fetching accumulates data over time
- prepare-data-v2.py reads Parquet files and converts to JSON for the static site

**Key Files:**
- `config/sources/financial.yaml` - cdata dataset configurations (28 sources)
- `data/index.json` - cdata metadata tracking (generated)
- `data/raw/*.parquet` - cdata Parquet storage (generated, 3.7MB)
- `scripts/prepare-data-v2.py` - Reads Parquet, transforms to JSON
- `public/data/*.json` - JSON files for client-side visualization (36MB)
- `src/data/datasets.json` - Summary for static site generation
- `src/pages/data/[dataset].astro` - Dynamic dataset pages

## Current Data Flow

```
cdata Configuration (config/sources/financial.yaml)
  ↓ 28 data sources defined
  ↓
cdata fetch all
  ↓ Fetches from APIs (Yahoo Finance, FRED, BLS, RSS, etc.)
  ↓ Stores in data/raw/*.parquet (3.7MB)
  ↓ Updates data/index.json metadata
  ↓ Incremental: only fetches new records since last update
  ↓
prepare-data-v2.py
  ↓ Reads from Parquet storage
  ↓ Transforms to JSON
  ↓ Writes to: public/data/*.json (36MB) + src/data/datasets.json
  ↓
Astro Build
  ↓ Generates 32 static HTML pages from datasets.json
  ↓ Includes full data JSON files for client-side Plotly charts
  ↓
GitHub Pages (deployed site: 46MB)
```

## cdata Integration

This project uses cdata as a **local data management system** rather than as a separate pipeline or library import.

### Benefits of Local cdata Instance

| Aspect | Description |
|--------|-------------|
| **Incremental Updates** | cdata tracks `last_record_date` and only fetches new data |
| **Efficient Storage** | Parquet format compresses 233K records to 3.7MB |
| **Single Source** | One project manages both data and presentation |
| **Simple Workflow** | `cdata fetch all` → `npm run build` → deployed |
| **Data Accumulation** | Data grows over time, not regenerated fresh each build |

### Storage Structure

```
data/
├── index.json              # cdata metadata (last_record_date, fetch_count)
└── raw/
    ├── us_indices.parquet
    ├── fred_gdp.parquet
    ├── bls_employment.parquet
    └── ... (28 datasets total)
```

## Working with Data

### Initial Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set up API keys (required for FRED, BLS)
cp .env.example .env
# Edit .env and add your FRED_API_KEY

# Initialize cdata (already done)
python3 -m cdata init

# Fetch initial data (233K records, ~2 minutes)
python3 -m cdata fetch all

# Generate JSON for site
python3 scripts/prepare-data-v2.py

# Build site
npm run build
```

### Updating Data

```bash
# Fetch updates (only new records since last fetch)
python3 -m cdata fetch all
# Example: Second run fetched only 1,049 new records

# Regenerate JSON
python3 scripts/prepare-data-v2.py

# Rebuild site
npm run build
# Or use npm script that does both:
npm run build  # runs prepare-data-v2.py then astro build
```

### Adding New Data Sources

1. Edit `config/sources/financial.yaml`:
   ```yaml
   sources:
     - id: my_new_source
       name: "My New Data"
       type: yfinance  # or fred, bls, rss, etc.
       enabled: true
       description: "Description here"
       primary_keys: ["symbol", "date"]
       incremental: true
       config:
         symbols: [AAPL, MSFT]
         period: "1y"
         interval: "1d"
   ```

2. Fetch the new source:
   ```bash
   python3 -m cdata fetch source my_new_source
   ```

3. Update `scripts/prepare-data-v2.py` if needed:
   - Add to OHLCV_DATASETS, RSS_DATASETS, FRED_DATASETS, or BLS_DATASETS
   - Or add new processing function for custom types

4. Regenerate and rebuild:
   ```bash
   python3 scripts/prepare-data-v2.py
   npm run build
   ```

### Data Freshness

- cdata tracks `last_record_date` for each dataset
- `fetch_count` shows how many times data has been updated
- Incremental fetching uses `since=last_record_date` parameter
- DataFreshness.astro component shows age indicators on site

## Dataset Types

### OHLCV (Price Data)
- **Sources:** yfinance
- **Columns:** symbol, date, open, high, low, close, volume
- **Examples:** us_indices, commodities, bond_etfs
- **Processing:** `prepare_ohlcv_dataset()` computes per-symbol statistics

### RSS (News Feeds)
- **Sources:** RSS feeds
- **Columns:** title, link, published, feed_name, author
- **Examples:** fed_news, financial_news, economics_news
- **Processing:** `prepare_rss_dataset()` shows recent 30 articles

### FRED (Federal Reserve Economic Data)
- **Sources:** FRED API
- **Columns:** series_id, date, value, title, units, frequency
- **Examples:** fred_gdp, fred_employment, fred_inflation
- **Processing:** `prepare_fred_dataset()` computes per-series statistics
- **Note:** Requires FRED_API_KEY in .env

### BLS (Bureau of Labor Statistics)
- **Sources:** BLS API
- **Columns:** series_id, date, value, title, units
- **Examples:** bls_cpi, bls_employment, bls_wages
- **Processing:** Same as FRED (uses `prepare_fred_dataset()`)

### Fed Stress Test Scenarios
- **Sources:** Federal Reserve DFAST stress test data
- **Columns:** year, scenario, table, date, variable, value
- **Example:** fed_stress_scenarios
- **Processing:** Not yet implemented in prepare-data-v2.py

## Development Workflow

### Local Development

```bash
# Start dev server (use Windows Node for proper networking)
"/mnt/c/Program Files/nodejs/npm" run dev --host

# Available at: http://localhost:4321/the-derple-dex
```

### Adding Visualizations

1. Create component in `src/components/data/`
2. Use Plotly.js for interactive charts
3. Follow existing patterns:
   - `TimeSeriesPlot.astro` - Line/candlestick charts
   - `NewsTimeline.astro` - Article lists
   - `DatasetStats.astro` - Summary tables

### Component Architecture

```
src/pages/data/
  ├── index.astro           # Landing page listing all datasets
  └── [dataset].astro       # Dynamic pages for each dataset

src/components/data/
  ├── DatasetCard.astro     # Preview card on landing page
  ├── DataFreshness.astro   # Shows data age/staleness
  ├── DatasetStats.astro    # Summary statistics table
  ├── TimeSeriesPlot.astro  # Plotly line/candlestick charts
  └── NewsTimeline.astro    # RSS article list
```

## Current Datasets

**Total:** 28 datasets, 233K initial records

**Market Data (8):**
- us_indices - Major US equity indices (S&P 500, Dow, NASDAQ, Russell 2000, VIX)
- global_indices - International indices (FTSE, DAX, Nikkei, etc.)
- treasury_yields - Treasury yield curve (13-week, 5Y, 10Y, 30Y)
- bond_etfs - Fixed income ETFs (TLT, AGG, HYG, etc.)
- currencies - Dollar index and major pairs
- commodities - Gold, silver, oil, copper, etc.
- sector_etfs - S&P 500 sector performance
- macro_proxies - ETFs tracking macro themes

**News Feeds (3):**
- fed_news - Federal Reserve press releases and speeches
- financial_news - Market news (Yahoo, Seeking Alpha, CNBC)
- economics_news - Economic analysis (Calculated Risk, Marginal Revolution)

**FRED Economic Data (11):**
- fred_gdp - GDP and output measures
- fred_employment - Employment and labor market
- fred_inflation - CPI, PCE, PPI inflation measures
- fred_rates - Fed funds, Treasury yields, spreads
- fred_money - M1, M2, Fed balance sheet
- fred_housing - Housing starts, sales, prices
- fred_consumer - Retail sales, consumer sentiment
- fred_banking - H.8 commercial banking data
- fred_stress_index - Financial stress indices
- fred_mev - Macro scenario variables
- fred_market - Market snapshot (S&P 500, VIX, spreads)

**BLS Labor Data (5):**
- bls_cpi - Consumer Price Index
- bls_employment - Employment and unemployment
- bls_wages - Hourly and weekly earnings
- bls_ppi - Producer Price Index
- bls_jolts - Job openings and labor turnover

**Fed Stress Tests (1):**
- fed_stress_scenarios - DFAST stress test scenarios (baseline & severely adverse)

## Environment & Dependencies

**Node.js:** Use Windows Node (not WSL) for proper networking
- Location: `/mnt/c/Program Files/nodejs/npm`
- Reason: WSL networking issues with Astro dev server

**Python Dependencies:**
```
cdata @ git+https://github.com/kenEldridge/cdata.git@dev
pandas>=2.0
pyarrow>=14.0
python-dotenv>=1.0
```

**Astro Dependencies:**
- See `package.json` for full list

**API Keys Required:**
- `FRED_API_KEY` - Free from https://fred.stlouisfed.org/docs/api/api_key.html
- Store in `.env` file at project root

## Deployment

- **Host:** GitHub Pages
- **URL:** https://keneldridge.github.io/the-derple-dex/
- **CI/CD:** GitHub Actions on push to master
- **Base Path:** `/the-derple-dex` (configured in astro.config.mjs)
- **Build:** ~101 seconds (includes data generation)
- **Output:** 32 HTML pages, 46MB total

### CI/CD Pipeline

The GitHub Actions workflow should:
1. Set up Python and install dependencies
2. Set FRED_API_KEY secret
3. Run `cdata fetch all` to get latest data
4. Run `npm run build` (includes prepare-data-v2.py)
5. Deploy dist/ to GitHub Pages

**Note:** May need to commit Parquet files or regenerate on each build. Current approach regenerates to ensure freshness.

## File Size Summary

| Location | Size | Description |
|----------|------|-------------|
| `data/raw/*.parquet` | 3.7MB | cdata Parquet storage (28 files) |
| `public/data/*.json` | 36MB | JSON for client-side charts (27 files) |
| `dist/` | 46MB | Built static site (32 HTML pages) |

**Why JSON is larger than Parquet:**
- Parquet uses columnar compression
- JSON includes full metadata and string formatting
- JSON optimized for client-side JavaScript parsing
- Trade-off: file size vs. browser compatibility

## Git Ignore Strategy

**Current approach:**
- `.gitignore` should exclude `data/raw/*.parquet` (generated)
- `.gitignore` should exclude `data/index.json` (generated)
- `public/data/*.json` can be tracked OR regenerated in CI/CD
- `dist/` is excluded (build output)

**Rationale:** Parquet files grow over time and can be regenerated from sources. JSON files are build artifacts.

## Known Issues

1. **Yahoo Finance Date Errors:** Some symbols show "possibly delisted" errors when fetching incrementally (start date > end date). This is a Yahoo Finance API quirk and doesn't affect data quality.

2. **Fed Stress Scenarios:** Not yet handled in prepare-data-v2.py. Need to add processing function for this dataset type.

3. **Pandas Future Warnings:** Mixed timezone warnings in date parsing. Non-breaking but should be fixed with `utc=True` parameter.

## Future Enhancements

- [ ] Add fed_stress processing function
- [ ] Implement data download functionality (CSV/JSON)
- [ ] Add client-side filtering/search
- [ ] Add comparison charts (multiple series overlaid)
- [ ] Add technical indicators (SMA, RSI, Bollinger Bands)
- [ ] Add SEC EDGAR company filings integration
- [ ] Add NIC BHC bank holding company data
- [ ] Optimize JSON file sizes (chunking, lazy loading)

## Related Resources

- [cdata repository](https://github.com/kenEldridge/cdata)
- [cdata issue #4: Bridge Pattern Discussion](https://github.com/kenEldridge/cdata/issues/4)
- [Astro documentation](https://docs.astro.build)
- [Plotly.js documentation](https://plotly.com/javascript/)
- [FRED API documentation](https://fred.stlouisfed.org/docs/api/fred/)
- [BLS API documentation](https://www.bls.gov/developers/)

## Troubleshooting

**"Error: cdata index not found at data/index.json"**
- Run `python3 -m cdata fetch all` first to initialize data

**"No such file or directory: data/raw/[dataset].parquet"**
- Dataset may not be enabled or failed to fetch
- Check `config/sources/financial.yaml` for `enabled: true`
- Check cdata fetch output for errors

**Build fails with memory errors**
- Large JSON files can cause OOM during build
- Consider reducing dataset sizes or chunking data
- Exit code 137 usually indicates OOM killer

**Missing FRED data**
- Ensure `FRED_API_KEY` is set in `.env` file
- Check that `.env` file is in project root
- Verify API key is valid at https://fred.stlouisfed.org/

**Stale data on site**
- Run `python3 -m cdata fetch all` to update Parquet files
- Run `python3 scripts/prepare-data-v2.py` to regenerate JSON
- Rebuild with `npm run build`
