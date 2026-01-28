# the-derple-dex - Project Guide for AI Assistants

This is a technical blog and data showcase site built with Astro. It displays financial and economic data collected via [cdata](https://github.com/kenEldridge/cdata).

## Architecture Overview

**Current Approach:** File-based data consumption
- `cdata` runs as a standalone data pipeline (separate project at `../cdata`)
- `cdata` fetches data on schedule and writes Parquet files
- This project reads those Parquet files and converts them to JSON at build time
- Static site generation with pre-rendered data pages

**Key Files:**
- `scripts/prepare-data.py` - Converts cdata Parquet → JSON for Astro
- `src/pages/data/[dataset].astro` - Dynamic dataset pages
- `src/components/data/*` - Data visualization components

## Current Data Flow

```
cdata (separate project)
  ↓ Fetches data on schedule
  ↓ Writes to: ../cdata/data/*.parquet
  ↓
prepare-data.py
  ↓ Reads Parquet files
  ↓ Transforms to JSON
  ↓ Writes to: public/data/*.json + src/data/datasets.json
  ↓
Astro Build
  ↓ Generates static pages from datasets.json
  ↓ Includes full data JSON files for client-side charts
  ↓
GitHub Pages (deployed site)
```

## Alternative: Bridge Pattern (Future Enhancement)

Issue [#4](https://github.com/kenEldridge/cdata/issues/4) documents using `cdata` as a **library** rather than reading its output files.

### Bridge Pattern Benefits

| Aspect | Current (File-based) | Bridge Pattern |
|--------|---------------------|----------------|
| **Separation** | Two projects, file coupling | Single project, API coupling |
| **Config** | YAML files in cdata | Python code in this project |
| **Storage** | cdata manages Parquet | This project manages storage |
| **Scheduling** | cdata's APScheduler | This project's control |
| **Data Flow** | Fetch → Parquet → JSON | Fetch → Custom processing → Storage |
| **Testing** | Hard to test data pipeline | Easy to mock fetches |

### Bridge Pattern Example

```python
# scripts/fetch_with_bridge.py
from cdata.core.registry import get_registry
from cdata.config.schema import SourceConfig

class CDataBridge:
    """Bridge to cdata framework - this project owns config and storage."""

    def __init__(self):
        self._registry = None

    @property
    def registry(self):
        if self._registry is None:
            self._registry = get_registry()
        return self._registry

    def fetch_market_data(self, symbols: list[str]) -> pd.DataFrame:
        """Fetch market data using cdata, return as DataFrame."""
        config = SourceConfig(
            id="custom_market",
            name="Custom Market Data",
            type="yfinance",
            config={"symbols": symbols, "period": "1y"},
            primary_keys=["symbol", "date"]
        )
        source = self.registry.create_source(config)
        result = source.fetch()
        return pd.DataFrame([r.data for r in result.records])

    def fetch_fred_indicators(self, series: list[str]) -> pd.DataFrame:
        """Fetch FRED data using cdata."""
        config = SourceConfig(
            id="custom_fred",
            name="Custom FRED Data",
            type="fred",
            config={"series": series},
            primary_keys=["series_id", "date"]
        )
        source = self.registry.create_source(config)
        result = source.fetch()
        return pd.DataFrame([r.data for r in result.records])

# Usage in prepare-data.py
bridge = CDataBridge()
sp500_data = bridge.fetch_market_data(["^GSPC", "^DJI", "^IXIC"])
gdp_data = bridge.fetch_fred_indicators(["GDP", "UNRATE"])

# Now process and write JSON as usual
```

### When to Use Bridge Pattern

✅ **Use Bridge Pattern if:**
- You want full control over data processing and storage
- You need custom data transformations
- You want to integrate cdata into an existing data pipeline
- You need to test data fetches with mocks
- You're building a production service that needs programmatic control

⚠️ **Stick with File-based if:**
- You want a simple, decoupled architecture
- cdata's scheduling and storage work well for your needs
- You prefer configuration over code
- You don't need custom data processing
- You want to minimize code complexity

## Current Implementation: File-based Approach

**This project currently uses the file-based approach** because:
1. ✅ Simple and decoupled - blog and data pipeline are separate concerns
2. ✅ Easy to understand - clear separation of responsibilities
3. ✅ Works with existing cdata setup - no code changes needed
4. ✅ Flexible - can switch data sources by editing cdata YAML files
5. ✅ Cacheable - Parquet files can be versioned/backed up independently

### Working with the Current Approach

**To add a new data source:**
1. Add source config to `../cdata/config/sources/*.yaml`
2. Run `cdata fetch source <source_id>`
3. Add dataset name to appropriate set in `prepare-data.py` (OHLCV_DATASETS, etc.)
4. Run `python3 scripts/prepare-data.py`
5. Rebuild site with `npm run build`

**To refresh data:**
```bash
# From cdata project
cd ../cdata
cdata fetch all

# From this project
cd ../the-derple-dex
python3 scripts/prepare-data.py
npm run build
```

**Data location:**
- Source: `../cdata/data/*.parquet`
- Metadata: `../cdata/data/index.json`
- Build output: `public/data/*.json` (for client-side)
- Build output: `src/data/datasets.json` (for SSG)

## Development Workflow

### Local development
```bash
# Start dev server (use Windows Node)
"/mnt/c/Program Files/nodejs/npm" run dev --host

# Available at: http://localhost:4321/the-derple-dex
```

### Adding new visualizations
1. Create component in `src/components/data/`
2. Use Plotly.js for interactive charts
3. Follow existing patterns (TimeSeriesPlot.astro, NewsTimeline.astro)

### Data freshness
- Data pages show: first_fetched, last_updated, fetch_count
- Automated via `DataFreshness.astro` component

## Known Patterns and Conventions

### Dataset Types
- **OHLCV**: Price data (open, high, low, close, volume)
- **RSS**: News feeds with title, link, published, feed_name
- **FRED/BLS**: Economic time series with series_id, date, value

### Processing Functions
- `prepare_ohlcv_dataset()` - Handles price data, computes per-symbol stats
- `prepare_fred_dataset()` - Handles FRED/BLS, computes per-series stats
- `prepare_rss_dataset()` - Handles news feeds, computes daily article counts

### Component Architecture
```
src/pages/data/
  ├── index.astro           # Landing page with all datasets
  └── [dataset].astro       # Dynamic pages for each dataset

src/components/data/
  ├── DatasetCard.astro     # Preview card on landing page
  ├── DataFreshness.astro   # Shows data age/staleness
  ├── DatasetStats.astro    # Summary statistics table
  ├── TimeSeriesPlot.astro  # Plotly line/candlestick charts
  └── NewsTimeline.astro    # RSS article list
```

## Environment & Dependencies

**Node.js:** Use Windows Node (not WSL) for proper networking
- Location: `/mnt/c/Program Files/nodejs/npm`

**Python Dependencies:**
- pandas (for Parquet reading)
- pyarrow (for Parquet backend)

**Astro Dependencies:**
- See `package.json` for full list

## Deployment

- **Host:** GitHub Pages
- **URL:** https://keneldridge.github.io/the-derple-dex/
- **CI/CD:** GitHub Actions on push to master
- **Base Path:** `/the-derple-dex` (configured in astro.config.mjs)

## Data Sources

The site currently displays 11 datasets from cdata:

**Market Data (8):** us_indices, global_indices, treasury_yields, bond_etfs, currencies, commodities, sector_etfs, macro_proxies

**News Feeds (3):** fed_news, financial_news, economics_news

All sourced via yfinance and RSS feeds. See `../cdata/config/sources/` for full configs.

## Future Enhancements

Potential improvements:
- [ ] Implement bridge pattern for real-time data fetching
- [ ] Add more economic indicators (FRED, BLS)
- [ ] Add SEC EDGAR company filings
- [ ] Add NIC BHC bank holding company data
- [ ] Client-side data filtering/search
- [ ] Data download functionality (CSV/JSON)
- [ ] Comparison charts (multiple series)
- [ ] Technical indicators (SMA, RSI, etc.)

## Related Resources

- [cdata documentation](https://github.com/kenEldridge/cdata)
- [cdata issue #4: Library Integration Guide](https://github.com/kenEldridge/cdata/issues/4)
- [Astro documentation](https://docs.astro.build)
- [Plotly.js documentation](https://plotly.com/javascript/)
