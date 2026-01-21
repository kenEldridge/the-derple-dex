# the derple-dex

Ken Eldridge's technical blog and project showcase.

Built with Astro, deployed to GitHub Pages.

## Features

- ✅ Dark mode (toggle in header)
- ✅ Blog posts with dates and tags
- ✅ Syntax highlighting with GitHub Dark theme
- ✅ Responsive design
- ✅ SEO-friendly with canonical URLs and OpenGraph data
- ✅ Sitemap support
- ✅ RSS Feed support
- ✅ Markdown & MDX support
- ✅ **Data Explorer** - Interactive financial data pages powered by [cdata](https://github.com/kenEldridge/cdata)

## 🚀 Project Structure

Inside of your Astro project, you'll see the following folders and files:

```text
├── public/
├── src/
│   ├── components/
│   ├── content/
│   ├── layouts/
│   └── pages/
├── astro.config.mjs
├── README.md
├── package.json
└── tsconfig.json
```

Astro looks for `.astro` or `.md` files in the `src/pages/` directory. Each page is exposed as a route based on its file name.

There's nothing special about `src/components/`, but that's where we like to put any Astro/React/Vue/Svelte/Preact components.

The `src/content/` directory contains "collections" of related Markdown and MDX documents. Use `getCollection()` to retrieve posts from `src/content/blog/`, and type-check your frontmatter using an optional schema. See [Astro's Content Collections docs](https://docs.astro.build/en/guides/content-collections/) to learn more.

Any static assets, like images, can be placed in the `public/` directory.

## 🧞 Commands

All commands are run from the root of the project (`/mnt/c/Users/eldri/projects/the-derple-dex` from WSL).

**IMPORTANT:** Use Windows Node.js (not WSL Node) for proper networking and base path handling.

### Start the dev server

```bash
"/mnt/c/Program Files/nodejs/npm" run dev --host
```

The site will be available at: **http://localhost:4321/the-derple-dex**

### Stop the dev server

Press `Ctrl+C` in the terminal where the server is running.

### Restart the dev server

1. Stop it with `Ctrl+C`
2. Run the start command again

### Other commands

| Command                   | Action                                           |
| :------------------------ | :----------------------------------------------- |
| `npm install`             | Installs dependencies                            |
| `npm run build`           | Build your production site to `./dist/`          |
| `npm run preview`         | Preview your build locally, before deploying     |
| `npm run astro ...`       | Run CLI commands like `astro add`, `astro check` |
| `npm run astro -- --help` | Get help using the Astro CLI                     |

## 🌐 Deployment

- **Live site:** https://keneldridge.github.io/the-derple-dex/
- **GitHub repo:** https://github.com/kenEldridge/the-derple-dex
- **Deploys automatically** via GitHub Actions on push to master

## 📝 Adding New Blog Posts

### Simple posts (Markdown)
1. Create a new `.md` file in `src/content/blog/`
2. Add frontmatter and content

### Posts with interactive components (MDX)
1. Create a folder: `src/content/blog/your-post-name/`
2. Add `index.mdx` with frontmatter
3. Place images in the same folder, reference as `./image.png`
4. Import and use Astro components for interactive content

Example with local image:
```markdown
---
title: 'Your Post Title'
description: 'Brief description'
pubDate: 2026-01-16
heroImage: ./thumbnail.png
---

Your content here...
```

### Frontmatter options
- `title` (required)
- `description` (required)
- `pubDate` (required)
- `heroImage` (optional) - use `./image.png` for local, `/image.png` for public/

## 📊 Interactive Visualizations

The blog uses Plotly.js for interactive plots. See `src/components/PlotA.astro`, `PlotB.astro`, `PlotC.astro` for examples.

To add to a post:
1. Create component in `src/components/`
2. Import in your `.mdx` file: `import MyPlot from '../../../components/MyPlot.astro';`
3. Use in content: `<MyPlot />`

## 📈 Data Explorer

The site includes a data explorer that displays financial and economic data collected via [cdata](https://github.com/kenEldridge/cdata).

### Data Sources (11 datasets)

**Price Data (OHLCV):**
- `us_indices` - S&P 500, Dow, NASDAQ, Russell 2000, VIX
- `global_indices` - FTSE, DAX, Nikkei, Hang Seng, Euro Stoxx
- `treasury_yields` - 13-week, 5yr, 10yr, 30yr Treasury yields
- `bond_etfs` - TLT, IEF, SHY, AGG, LQD, HYG, TIP, MUB
- `currencies` - Dollar Index, EUR, GBP, JPY, CNY
- `commodities` - Gold, Silver, WTI, Brent, Natural Gas, Copper
- `sector_etfs` - All 10 S&P 500 sector ETFs
- `macro_proxies` - SPY, QQQ, IWM, GLD, etc.

**News Feeds (RSS):**
- `fed_news` - Federal Reserve press releases & speeches
- `financial_news` - Yahoo Finance, Seeking Alpha, CNBC
- `economics_news` - Calculated Risk, Marginal Revolution

### Refreshing Data

Data is fetched from cdata and converted to JSON at build time:

```bash
# Refresh data from cdata (requires cdata project at ../cdata)
python3 scripts/prepare-data.py

# Or use npm script
npm run prepare-data
```

### Data Page Features

Each dataset page includes:
- **Data Freshness** - First fetched, last updated, fetch count
- **Summary Statistics** - Date ranges, per-symbol stats
- **Interactive Charts** - Plotly candlestick/line charts (OHLCV data)
- **News Timeline** - Recent articles (RSS data)
- **Data Schema** - Column names and primary keys

### Project Structure (Data)

```
├── scripts/
│   └── prepare-data.py          # Converts parquet → JSON
├── src/
│   ├── components/data/
│   │   ├── DatasetCard.astro    # Landing page card
│   │   ├── DataFreshness.astro  # Freshness indicator
│   │   ├── DatasetStats.astro   # Summary stats table
│   │   ├── TimeSeriesPlot.astro # Plotly charts
│   │   └── NewsTimeline.astro   # RSS article list
│   ├── data/
│   │   └── datasets.json        # Generated metadata
│   └── pages/data/
│       ├── index.astro          # Landing page
│       └── [dataset].astro      # Dynamic dataset pages
└── public/data/
    └── *.json                   # Generated dataset files
```

## 👀 Want to learn more?

Check out [our documentation](https://docs.astro.build) or jump into our [Discord server](https://astro.build/chat).

## Credit

This theme is based off of the lovely [Bear Blog](https://github.com/HermanMartinus/bearblog/).
