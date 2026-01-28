"""
Dataset configurations for the-derple-dex.

This module defines all datasets that will be fetched and displayed on the site.
Configurations are used by cdata_bridge.py to programmatically fetch data.
"""

# Dataset configurations - maps dataset ID to its fetch configuration
DATASETS = {
    # ===================
    # US EQUITY INDICES
    # ===================
    "us_indices": {
        "name": "US Market Indices",
        "type": "yfinance",
        "description": "Major US equity indices",
        "config": {
            "symbols": ["^GSPC", "^DJI", "^IXIC", "^RUT", "^VIX"],
            "period": "1y",
            "interval": "1d"
        },
        "primary_keys": ["symbol", "date"]
    },

    # ===================
    # GLOBAL EQUITY INDICES
    # ===================
    "global_indices": {
        "name": "Global Market Indices",
        "type": "yfinance",
        "description": "Major international equity indices",
        "config": {
            "symbols": ["^FTSE", "^GDAXI", "^FCHI", "^N225", "^HSI", "^STOXX50E", "FXI", "EEM"],
            "period": "1y",
            "interval": "1d"
        },
        "primary_keys": ["symbol", "date"]
    },

    # ===================
    # US TREASURY YIELDS
    # ===================
    "treasury_yields": {
        "name": "US Treasury Yields",
        "type": "yfinance",
        "description": "Treasury yield curve data",
        "config": {
            "symbols": ["^IRX", "^FVX", "^TNX", "^TYX"],
            "period": "1y",
            "interval": "1d"
        },
        "primary_keys": ["symbol", "date"]
    },

    # ===================
    # BOND ETFs
    # ===================
    "bond_etfs": {
        "name": "Bond ETFs",
        "type": "yfinance",
        "description": "Fixed income ETFs across durations and types",
        "config": {
            "symbols": ["TLT", "IEF", "SHY", "AGG", "LQD", "HYG", "TIP", "MUB"],
            "period": "1y",
            "interval": "1d"
        },
        "primary_keys": ["symbol", "date"]
    },

    # ===================
    # CURRENCIES & DOLLAR
    # ===================
    "currencies": {
        "name": "Currencies & Dollar Index",
        "type": "yfinance",
        "description": "Dollar strength and major currency pairs",
        "config": {
            "symbols": ["DX-Y.NYB", "EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCNY=X"],
            "period": "1y",
            "interval": "1d"
        },
        "primary_keys": ["symbol", "date"]
    },

    # ===================
    # COMMODITIES
    # ===================
    "commodities": {
        "name": "Commodities",
        "type": "yfinance",
        "description": "Key commodity prices",
        "config": {
            "symbols": ["GC=F", "SI=F", "CL=F", "BZ=F", "NG=F", "HG=F"],
            "period": "1y",
            "interval": "1d"
        },
        "primary_keys": ["symbol", "date"]
    },

    # ===================
    # SECTOR ETFs
    # ===================
    "sector_etfs": {
        "name": "US Sector ETFs",
        "type": "yfinance",
        "description": "S&P 500 sector performance",
        "config": {
            "symbols": ["XLF", "XLK", "XLE", "XLV", "XLI", "XLP", "XLY", "XLU", "XLB", "XLRE"],
            "period": "1y",
            "interval": "1d"
        },
        "primary_keys": ["symbol", "date"]
    },

    # ===================
    # MACRO INDICATOR PROXIES
    # ===================
    "macro_proxies": {
        "name": "Macro Indicator Proxies",
        "type": "yfinance",
        "description": "ETFs that track macro themes",
        "config": {
            "symbols": ["SPY", "QQQ", "IWM", "DBA", "UUP", "GLD", "GOVT"],
            "period": "1y",
            "interval": "1d"
        },
        "primary_keys": ["symbol", "date"]
    },

    # ===================
    # FEDERAL RESERVE & POLICY NEWS
    # ===================
    "fed_news": {
        "name": "Federal Reserve News",
        "type": "rss",
        "description": "Federal Reserve announcements and speeches",
        "config": {
            "feeds": [
                {
                    "name": "Federal Reserve Press Releases",
                    "url": "https://www.federalreserve.gov/feeds/press_all.xml"
                },
                {
                    "name": "Fed Speeches",
                    "url": "https://www.federalreserve.gov/feeds/speeches.xml"
                }
            ]
        },
        "primary_keys": ["id"]
    },

    # ===================
    # FINANCIAL NEWS
    # ===================
    "financial_news": {
        "name": "Financial News",
        "type": "rss",
        "description": "Market and economic news feeds",
        "config": {
            "feeds": [
                {
                    "name": "Yahoo Finance",
                    "url": "https://finance.yahoo.com/news/rssindex"
                },
                {
                    "name": "Seeking Alpha Market News",
                    "url": "https://seekingalpha.com/market_currents.xml"
                },
                {
                    "name": "CNBC Top News",
                    "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114"
                }
            ]
        },
        "primary_keys": ["id"]
    },

    # ===================
    # ECONOMIC DATA NEWS
    # ===================
    "economics_news": {
        "name": "Economics & Policy News",
        "type": "rss",
        "description": "Economic analysis and policy coverage",
        "config": {
            "feeds": [
                {
                    "name": "Calculated Risk",
                    "url": "https://www.calculatedriskblog.com/feeds/posts/default?alt=rss"
                },
                {
                    "name": "Marginal Revolution",
                    "url": "https://marginalrevolution.com/feed"
                }
            ]
        },
        "primary_keys": ["id"]
    },

    # ===================
    # FRED - MACRO INDICATORS
    # ===================
    "fred_gdp": {
        "name": "GDP & Output",
        "type": "fred",
        "description": "Gross Domestic Product and related measures",
        "config": {
            "series": ["GDP", "GDPC1", "A191RL1Q225SBEA", "GDPDEF"]
        },
        "primary_keys": ["series_id", "date"]
    },

    "fred_employment": {
        "name": "Employment & Labor",
        "type": "fred",
        "description": "Employment, unemployment, and labor market indicators",
        "config": {
            "series": ["UNRATE", "PAYEMS", "ICSA", "JTSJOL", "AWHAETP", "CES0500000003"]
        },
        "primary_keys": ["series_id", "date"]
    },

    "fred_inflation": {
        "name": "Inflation & Prices",
        "type": "fred",
        "description": "Consumer and producer price indices",
        "config": {
            "series": ["CPIAUCSL", "CPILFESL", "PCEPI", "PCEPILFE", "PPIACO", "MICH"]
        },
        "primary_keys": ["series_id", "date"]
    },

    "fred_rates": {
        "name": "Interest Rates & Yields",
        "type": "fred",
        "description": "Federal Reserve rates and Treasury yields",
        "config": {
            "series": ["FEDFUNDS", "DFEDTARU", "DFEDTARL", "DGS2", "DGS10", "DGS30", "T10Y2Y", "T10Y3M", "BAMLH0A0HYM2"]
        },
        "primary_keys": ["series_id", "date"]
    },

    "fred_money": {
        "name": "Money Supply & Credit",
        "type": "fred",
        "description": "Monetary aggregates and credit conditions",
        "config": {
            "series": ["M1SL", "M2SL", "WALCL", "TOTRESNS", "TOTALSL"]
        },
        "primary_keys": ["series_id", "date"]
    },

    "fred_housing": {
        "name": "Housing & Real Estate",
        "type": "fred",
        "description": "Housing market indicators",
        "config": {
            "series": ["HOUST", "PERMIT", "HSN1F", "EXHOSLUSM495S", "CSUSHPINSA", "MORTGAGE30US"]
        },
        "primary_keys": ["series_id", "date"]
    },

    "fred_consumer": {
        "name": "Consumer & Retail",
        "type": "fred",
        "description": "Consumer spending and sentiment",
        "config": {
            "series": ["RSAFS", "PCE", "PSAVERT", "UMCSENT", "DSPIC96"]
        },
        "primary_keys": ["series_id", "date"]
    },

    "fred_banking": {
        "name": "Banking & Credit (H.8)",
        "type": "fred",
        "description": "H.8 commercial banking data and credit conditions",
        "config": {
            "series": ["TOTBKCR", "BUSLOANS", "CONSUMER", "RESIDUAL", "TOTLL", "DPSACBW027SBOG", "RCFD2170"]
        },
        "primary_keys": ["series_id", "date"]
    },

    "fred_stress_index": {
        "name": "Financial Stress Indices",
        "type": "fred",
        "description": "Composite financial stress and conditions indicators",
        "config": {
            "series": ["STLFSI2", "NFCI", "CFSI"]
        },
        "primary_keys": ["series_id", "date"]
    },

    "fred_mev": {
        "name": "Macro Scenario Variables (MEV)",
        "type": "fred",
        "description": "Key macroeconomic variables used in stress test scenario design",
        "config": {
            "series": ["GDPC1", "UNRATE", "CPIAUCSL", "DGS10", "CSUSHPINSA", "MORTGAGE30US", "DTWEXBGS", "VIXCLS"]
        },
        "primary_keys": ["series_id", "date"]
    },

    "fred_market": {
        "name": "Market Snapshot",
        "type": "fred",
        "description": "Broad market indicators and risk measures",
        "config": {
            "series": ["SP500", "VIXCLS", "DTWEXBGS", "BAMLH0A0HYM2", "BAMLC0A0CM", "TEDRATE", "T10YIE"]
        },
        "primary_keys": ["series_id", "date"]
    },

    # ===================
    # BLS - LABOR STATISTICS
    # ===================
    "bls_cpi": {
        "name": "BLS Consumer Price Index",
        "type": "bls",
        "description": "CPI inflation measures from Bureau of Labor Statistics",
        "config": {
            "series": ["CUSR0000SA0", "CUSR0000SA0L1E", "CUUR0000SA0"]
        },
        "primary_keys": ["series_id", "date"]
    },

    "bls_employment": {
        "name": "BLS Employment",
        "type": "bls",
        "description": "Employment and unemployment from Bureau of Labor Statistics",
        "config": {
            "series": ["LNS14000000", "LNS11000000", "CES0000000001", "CES0500000001"]
        },
        "primary_keys": ["series_id", "date"]
    },

    "bls_wages": {
        "name": "BLS Wages & Earnings",
        "type": "bls",
        "description": "Wage and earnings data from Bureau of Labor Statistics",
        "config": {
            "series": ["CES0500000003", "CES0500000011"]
        },
        "primary_keys": ["series_id", "date"]
    },

    "bls_ppi": {
        "name": "BLS Producer Price Index",
        "type": "bls",
        "description": "Producer prices from Bureau of Labor Statistics",
        "config": {
            "series": ["WPUFD4", "WPSFD4", "WPUFD49104"]
        },
        "primary_keys": ["series_id", "date"]
    },

    "bls_jolts": {
        "name": "BLS JOLTS",
        "type": "bls",
        "description": "Job Openings and Labor Turnover Survey",
        "config": {
            "series": ["JTS000000000000000JOL", "JTS000000000000000HIR", "JTS000000000000000QUL", "JTS000000000000000TSL"]
        },
        "primary_keys": ["series_id", "date"]
    },
}
