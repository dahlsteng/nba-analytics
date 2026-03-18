# Scoring Volatility Analysis

Measures game-to-game scoring consistency for NBA players using **Coefficient of Variation (CV)**, defined as `StdDev / PPG`. A lower CV means a player's scoring output is more predictable; a higher CV means more boom-or-bust variance.

## Key Findings

- **Strong inverse correlation (r ≈ -0.68)** between PPG and CV — higher-volume scorers are significantly more predictable game-to-game.
- **Raw StdDev correlates positively with PPG (r ≈ 0.89)** — stars have bigger absolute swings, but smaller *relative* ones.
- **Clear tier staircase**: Elite scorers (25+ PPG) cluster near CV 0.35, while deep bench players (<5 PPG) average CV 1.5+.
- **Notable outliers among stars**: Some 20+ PPG scorers show unusually high volatility (CV > 0.50), making them boom-or-bust performers despite elite volume.

## Two Analysis Variants

| Script | Date Range | Min Minutes | Min Games | Output Folder |
|--------|-----------|-------------|-----------|---------------|
| `analysis_current.py` | Oct 22 2024 – Mar 18 2026 | > 0 | 15 | `output_current/` |
| `analysis_historical.py` | Oct 12 1979 – Mar 18 2026 | ≥ 15 | 20 | `output_historical/` |

The historical variant uses a 15-minute floor to filter out garbage-time appearances that inflate CV artificially over 45+ years of data.

## Running

From the `scoring-volatility/` directory:

```bash
# Current season
python analysis_current.py

# Historical (3-point era)
python analysis_historical.py
```

Each script produces:
- `player_scoring_volatility.csv` — full computed dataset
- `01_ppg_vs_volatility_scatter.png` — main insight chart
- `02_volatility_by_tier_boxplot.png` — CV distribution by PPG tier
- `03_consistent_vs_volatile.png` — head-to-head comparison (15+ PPG)
- `04_stddev_vs_ppg_scatter.png` — absolute swings vs volume
- `05_cv_distribution_histogram.png` — overall CV distribution
- `scoring_volatility_dashboard.html` — interactive dashboard with filters

## Methodology

1. Load game-level player statistics from `../../data/PlayerStatistics.csv`
2. Filter to date range, Regular Season + Playoffs, minimum minutes
3. Aggregate per player: PPG, StdDev, median, min, max, games played
4. Compute CV = StdDev / PPG
5. Assign PPG tiers (Elite, Star, Starter, Rotation, Bench, Deep Bench)
6. Filter to minimum games threshold
7. Generate static charts (matplotlib) and interactive HTML dashboard (Chart.js)

## Dashboard Features

- **Dynamic axis scaling** — all charts rescale when filters change
- **Filters** — Min PPG, Min Games, Tier, Player/Team search
- **Sortable table** — click any column header
- **KPI cards** — top scorer, most consistent, most volatile update live
- **Responsive** — works on desktop and mobile
