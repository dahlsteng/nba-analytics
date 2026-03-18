# NBA Analytics

A collection of data-driven NBA analysis projects built with Python, matplotlib, and interactive HTML dashboards.

## Setup

**Requirements:** Python 3.10+

```bash
pip install -r requirements.txt
```

**Data:** This repo expects a `PlayerStatistics.csv` file in the `data/` directory. The file contains game-level player statistics from 1946 to present (~300MB, excluded from version control). Place your copy there before running any scripts.

## Projects

### [Scoring Volatility](projects/scoring-volatility/)
Measures game-to-game scoring consistency using Coefficient of Variation (CV = StdDev / PPG). Identifies the most and least predictable scorers across different eras and scoring tiers.

- **Current season analysis** — 2024–26 season, all minutes
- **Historical analysis** — 1979–present (3-point era), 15+ minute filter

Each produces 5 PNG charts, an interactive HTML dashboard, and a CSV export.

## Repo Structure

```
nba-analytics/
├── README.md
├── requirements.txt
├── .gitignore
├── LICENSE
├── data/                          # Local only (gitignored)
│   └── PlayerStatistics.csv
├── projects/
│   └── scoring-volatility/
│       ├── README.md
│       ├── analysis_current.py
│       ├── analysis_historical.py
│       ├── output_current/        # Generated charts & dashboard
│       └── output_historical/     # Generated charts & dashboard
└── shared/                        # Shared utilities (as needed)
```

## License

MIT
