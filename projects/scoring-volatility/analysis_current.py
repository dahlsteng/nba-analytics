"""
NBA Player Scoring Volatility Analysis
=======================================
Analyzes player scoring consistency/volatility for the 2024-26 season
using Coefficient of Variation (CV = StdDev / PPG).

Design: Clean, usability-first aesthetic inspired by Nielsen Norman Group
principles — high contrast, clear hierarchy, generous whitespace,
maximized data-ink ratio, accessible color palette.

Outputs:
  - 5 PNG chart images
  - 1 interactive HTML dashboard
  - 1 CSV of the computed player stats

Date range: Oct 22, 2024 – Mar 18, 2026
Source: PlayerStatistics.csv (1946–present)
"""

import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import FancyBboxPatch
import os

# ──────────────────────────────────────────────
# CONFIGURATION — Update these paths if needed
# ──────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV  = os.path.join(SCRIPT_DIR, '..', '..', 'data', 'PlayerStatistics.csv')
OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'output_current')

START_DATE  = '2024-10-22'
END_DATE    = '2026-03-18'
MIN_GAMES   = 15          # Minimum games to include a player (filters noise)
MIN_MINUTES = 0           # Exclude games where player logged 0 minutes

# ──────────────────────────────────────────────
# SETUP
# ──────────────────────────────────────────────
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("Loading CSV (this may take a moment for 300MB+)...")
df = pd.read_csv(INPUT_CSV, low_memory=False)
print(f"  Loaded {len(df):,} rows")

# ──────────────────────────────────────────────
# 1. FILTER & CLEAN
# ──────────────────────────────────────────────
df['gameDateTimeEst'] = pd.to_datetime(df['gameDateTimeEst'])
mask = (df['gameDateTimeEst'] >= START_DATE) & (df['gameDateTimeEst'] <= END_DATE)
df_filtered = df.loc[mask].copy()

# Force numMinutes to numeric (handles stray strings / blanks)
df_filtered['numMinutes'] = pd.to_numeric(df_filtered['numMinutes'], errors='coerce')
df_filtered = df_filtered[df_filtered['numMinutes'] > MIN_MINUTES]

valid_types = ['Regular Season', 'Playoffs']
df_filtered = df_filtered[df_filtered['gameType'].isin(valid_types)]
print(f"  Filtered to {len(df_filtered):,} game rows in date range")

# ──────────────────────────────────────────────
# 2. AGGREGATE PER PLAYER
# ──────────────────────────────────────────────
grouped = df_filtered.groupby(['personId', 'firstName', 'lastName'])
agg = grouped.agg(
    PPG=('points', 'mean'),
    StdDev=('points', 'std'),
    avgMinutes=('numMinutes', 'mean'),
    gamesPlayed=('gameId', 'count'),
    totalPoints=('points', 'sum'),
    medianPoints=('points', 'median'),
    maxPoints=('points', 'max'),
    minPoints=('points', 'min'),
).reset_index()

# Most recent team
df_filtered = df_filtered.sort_values('gameDateTimeEst')
latest_team = df_filtered.groupby('personId').last().reset_index()[['personId', 'playerteamName']]
agg = agg.merge(latest_team, on='personId', how='left').rename(columns={'playerteamName': 'team'})

# Compute CV
agg['CV'] = agg['StdDev'] / agg['PPG']
agg['pointRange'] = agg['maxPoints'] - agg['minPoints']

# Filter to minimum games threshold
agg = agg[agg['gamesPlayed'] >= MIN_GAMES].copy()
agg = agg.sort_values('CV', ascending=False)

print(f"  {len(agg)} players with {MIN_GAMES}+ games")

# ──────────────────────────────────────────────
# 3. PPG TIERS
# ──────────────────────────────────────────────
def assign_tier(ppg):
    if ppg >= 25: return '25+ PPG (Elite)'
    if ppg >= 20: return '20-25 PPG (Star)'
    if ppg >= 15: return '15-20 PPG (Starter)'
    if ppg >= 10: return '10-15 PPG (Rotation)'
    if ppg >= 5:  return '5-10 PPG (Bench)'
    return '<5 PPG (Deep Bench)'

tier_order = ['25+ PPG (Elite)', '20-25 PPG (Star)', '15-20 PPG (Starter)',
              '10-15 PPG (Rotation)', '5-10 PPG (Bench)', '<5 PPG (Deep Bench)']

agg['tier'] = agg['PPG'].apply(assign_tier)
agg['tier'] = pd.Categorical(agg['tier'], categories=tier_order, ordered=True)

# ──────────────────────────────────────────────
# 4. SAVE CSV
# ──────────────────────────────────────────────
csv_out = os.path.join(OUTPUT_DIR, 'player_scoring_volatility.csv')
agg.to_csv(csv_out, index=False)
print(f"  CSV saved to: {csv_out}")

# ══════════════════════════════════════════════
# CHART STYLING
#
# Design principles (NNG-inspired):
#   - Light background: high readability, print-friendly
#   - Muted gridlines recede behind data points
#   - Accessible palette: all colors pass WCAG AA on white
#   - Left-aligned titles act as scannable headlines
#   - Descriptive subtitles eliminate guesswork
#   - Source line for provenance on every chart
#   - No spines top/right — reduced chart junk
#   - Generous figure padding
# ══════════════════════════════════════════════
BG       = '#FAFAFA'
CARD_BG  = '#FFFFFF'
TEXT     = '#1A1A2E'
LABEL    = '#4A4A68'
SUBTLE   = '#9494AD'
ACCENT   = '#2563EB'
ACCENT2  = '#DC2626'
GREEN    = '#059669'
GRID     = '#E8E8F0'

tier_colors = {
    '25+ PPG (Elite)':      '#B45309',
    '20-25 PPG (Star)':     '#DC2626',
    '15-20 PPG (Starter)':  '#2563EB',
    '10-15 PPG (Rotation)': '#059669',
    '5-10 PPG (Bench)':     '#7C7C98',
    '<5 PPG (Deep Bench)':  '#B8B8CC',
}

plt.rcParams.update({
    'figure.facecolor': BG,
    'axes.facecolor': CARD_BG,
    'text.color': TEXT,
    'axes.labelcolor': LABEL,
    'xtick.color': SUBTLE,
    'ytick.color': SUBTLE,
    'axes.edgecolor': GRID,
    'grid.color': GRID,
    'grid.alpha': 0.8,
    'grid.linewidth': 0.6,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica Neue', 'Helvetica', 'DejaVu Sans'],
    'font.size': 11,
    'axes.titlesize': 16,
    'axes.titleweight': 'bold',
    'axes.labelsize': 12,
    'axes.spines.top': False,
    'axes.spines.right': False,
})

def save_chart(fig, name):
    path = os.path.join(OUTPUT_DIR, name)
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  Chart saved: {path}")

def add_source_note(fig, y=-0.02):
    fig.text(0.01, y,
             f'Data: NBA PlayerStatistics  |  {START_DATE} to {END_DATE}  |  Min {MIN_GAMES} games',
             fontsize=8, color=SUBTLE, ha='left', va='top')

# ──────────────────────────────────────────────
# CHART 1: PPG vs CV Scatter (Main Insight)
# ──────────────────────────────────────────────
print("\nGenerating Chart 1: PPG vs Volatility scatter...")
fig, ax = plt.subplots(figsize=(13, 8.5))
fig.subplots_adjust(top=0.88)

for tier in tier_order:
    subset = agg[agg['tier'] == tier]
    ax.scatter(subset['PPG'], subset['CV'], c=tier_colors[tier],
               s=subset['gamesPlayed'] * 0.5 + 8, alpha=0.55,
               edgecolors='white', linewidth=0.3, label=tier, zorder=3)

notable = agg[agg['PPG'] >= 15].copy()
top_vol = notable.nlargest(8, 'CV')
bot_vol = notable.nsmallest(8, 'CV')
to_label = pd.concat([top_vol, bot_vol]).drop_duplicates()

for _, row in to_label.iterrows():
    name = f"{row['firstName'][0]}. {row['lastName']}"
    ax.annotate(name, (row['PPG'], row['CV']),
                fontsize=8, color=TEXT, fontweight='medium',
                textcoords='offset points', xytext=(7, 5),
                arrowprops=dict(arrowstyle='-', color=SUBTLE, lw=0.6, shrinkB=3))

z = np.polyfit(agg['PPG'], agg['CV'], 2)
p = np.poly1d(z)
x_line = np.linspace(agg['PPG'].min(), agg['PPG'].max(), 200)
ax.plot(x_line, p(x_line), color=ACCENT2, linewidth=1.8, linestyle='--', alpha=0.5, zorder=2)

ax.set_xlabel('Points Per Game (PPG)')
ax.set_ylabel('Coefficient of Variation (CV)')
fig.suptitle('Higher Scorers Are More Predictable', fontsize=20, fontweight='bold',
             color=TEXT, x=0.01, ha='left')
fig.text(0.01, 0.915,
         'Scoring volume vs game-to-game volatility — bubble size indicates games played',
         fontsize=11, color=SUBTLE, ha='left')
ax.legend(loc='upper right', fontsize=9, frameon=True, facecolor=CARD_BG,
          edgecolor=GRID, framealpha=0.95, borderpad=1)
ax.grid(True, alpha=0.5, zorder=1)
ax.set_xlim(left=0)
ax.set_ylim(bottom=0)
add_source_note(fig)
save_chart(fig, '01_ppg_vs_volatility_scatter.png')

# ──────────────────────────────────────────────
# CHART 2: Volatility by PPG Tier (Box Plot)
# ──────────────────────────────────────────────
print("Generating Chart 2: Volatility by tier box plot...")
fig, ax = plt.subplots(figsize=(11, 7))
fig.subplots_adjust(top=0.88)

tier_data = [agg[agg['tier'] == t]['CV'].dropna().values for t in tier_order]
bp = ax.boxplot(tier_data, labels=[t.split(' (')[0] for t in tier_order],
                patch_artist=True, widths=0.55, showfliers=False,
                medianprops=dict(color=TEXT, linewidth=2.5),
                whiskerprops=dict(color=SUBTLE, linewidth=1),
                capprops=dict(color=SUBTLE, linewidth=1))

for patch, tier in zip(bp['boxes'], tier_order):
    patch.set_facecolor(tier_colors[tier])
    patch.set_alpha(0.25)
    patch.set_edgecolor(tier_colors[tier])
    patch.set_linewidth(1.5)

for i, tier in enumerate(tier_order):
    subset = agg[agg['tier'] == tier]['CV'].dropna().values
    jitter = np.random.normal(0, 0.07, size=len(subset))
    ax.scatter(np.full_like(subset, i + 1) + jitter, subset,
               c=tier_colors[tier], alpha=0.25, s=12, edgecolors='none', zorder=3)

ax.set_ylabel('Coefficient of Variation (CV)')
fig.suptitle('Volatility Drops Steadily With Scoring Volume', fontsize=20,
             fontweight='bold', color=TEXT, x=0.01, ha='left')
fig.text(0.01, 0.915,
         'Distribution of CV across PPG tiers — median shown as dark line',
         fontsize=11, color=SUBTLE, ha='left')
ax.grid(True, axis='y', alpha=0.5)
ax.tick_params(axis='x', labelsize=10)
add_source_note(fig)
save_chart(fig, '02_volatility_by_tier_boxplot.png')

# ──────────────────────────────────────────────
# CHART 3: Most Consistent vs Most Volatile (15+ PPG)
# ──────────────────────────────────────────────
print("Generating Chart 3: Consistent vs Volatile comparison...")
qualifiers = agg[agg['PPG'] >= 15].copy()
most_consistent = qualifiers.nsmallest(10, 'CV')
most_volatile   = qualifiers.nlargest(10, 'CV')

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7.5), sharey=False)
fig.subplots_adjust(top=0.88, wspace=0.45)

def make_barh(ax, data, color, title):
    names = data.apply(lambda r: f"{r['firstName'][0]}. {r['lastName']}", axis=1).values
    teams = data['team'].values
    cvs = data['CV'].values
    ppgs = data['PPG'].values

    bars = ax.barh(range(len(data)), cvs, color=color, alpha=0.75,
                   edgecolor='none', height=0.65, zorder=3)
    ax.set_yticks(range(len(data)))
    ax.set_yticklabels(names, fontsize=10.5, fontweight='medium')
    ax.set_xlabel('Coefficient of Variation (CV)', fontsize=11)
    ax.set_title(title, fontsize=14, fontweight='bold', pad=12, loc='left')
    ax.grid(True, axis='x', alpha=0.4, zorder=1)
    ax.invert_yaxis()

    for j, (bar, ppg, team) in enumerate(zip(bars, ppgs, teams)):
        ax.text(bar.get_width() + 0.008, bar.get_y() + bar.get_height()/2,
                f'{ppg:.1f} ppg  ·  {team}', va='center', fontsize=9, color=SUBTLE)

make_barh(ax1, most_consistent, GREEN,   'Most Consistent')
make_barh(ax2, most_volatile,   ACCENT2, 'Most Volatile')
fig.suptitle('Consistency vs Volatility Among 15+ PPG Scorers',
             fontsize=20, fontweight='bold', color=TEXT, x=0.01, ha='left')
fig.text(0.01, 0.915,
         'Ranked by Coefficient of Variation — lower CV = more predictable output',
         fontsize=11, color=SUBTLE, ha='left')
add_source_note(fig)
save_chart(fig, '03_consistent_vs_volatile.png')

# ──────────────────────────────────────────────
# CHART 4: StdDev vs PPG (absolute swings)
# ──────────────────────────────────────────────
print("Generating Chart 4: StdDev vs PPG scatter...")
fig, ax = plt.subplots(figsize=(12, 8))
fig.subplots_adjust(top=0.88)

for tier in tier_order:
    subset = agg[agg['tier'] == tier]
    ax.scatter(subset['PPG'], subset['StdDev'], c=tier_colors[tier],
               s=25, alpha=0.45, edgecolors='white', linewidth=0.2, label=tier, zorder=3)

z2 = np.polyfit(agg['PPG'], agg['StdDev'], 1)
p2 = np.poly1d(z2)
x_l = np.linspace(0, agg['PPG'].max(), 200)
ax.plot(x_l, p2(x_l), color=ACCENT, linewidth=2, linestyle='-', alpha=0.6, zorder=4)

corr_val = agg['PPG'].corr(agg['StdDev'])
ax.text(0.96, 0.06, f'r = {corr_val:.2f}', transform=ax.transAxes,
        fontsize=16, color=ACCENT, fontweight='bold', ha='right',
        bbox=dict(boxstyle='round,pad=0.4', facecolor=CARD_BG, edgecolor=GRID, alpha=0.9))

ax.set_xlabel('Points Per Game (PPG)')
ax.set_ylabel('Standard Deviation of Points')
fig.suptitle('Absolute Point Swings Rise With Scoring Volume', fontsize=20,
             fontweight='bold', color=TEXT, x=0.01, ha='left')
fig.text(0.01, 0.915,
         'Raw StdDev vs PPG — stars have bigger absolute swings, but smaller relative ones',
         fontsize=11, color=SUBTLE, ha='left')
ax.legend(loc='upper left', fontsize=9, frameon=True, facecolor=CARD_BG,
          edgecolor=GRID, framealpha=0.95, borderpad=1)
ax.grid(True, alpha=0.5, zorder=1)
ax.set_xlim(left=0)
ax.set_ylim(bottom=0)
add_source_note(fig)
save_chart(fig, '04_stddev_vs_ppg_scatter.png')

# ──────────────────────────────────────────────
# CHART 5: CV Distribution Histogram
# ──────────────────────────────────────────────
print("Generating Chart 5: CV distribution histogram...")
fig, ax = plt.subplots(figsize=(12, 6))
fig.subplots_adjust(top=0.85)

cv_data = agg['CV'].clip(upper=3)
ax.hist(cv_data, bins=60, color=ACCENT, alpha=0.6, edgecolor=CARD_BG, linewidth=0.5, zorder=3)

median_cv = agg['CV'].median()
ax.axvline(median_cv, color=ACCENT2, linewidth=2, linestyle='--', alpha=0.8,
           label=f'Median: {median_cv:.2f}', zorder=4)

ax.set_xlabel('Coefficient of Variation (CV)')
ax.set_ylabel('Number of Players')
fig.suptitle('Most Players Cluster Below CV 1.5', fontsize=20,
             fontweight='bold', color=TEXT, x=0.01, ha='left')
fig.text(0.01, 0.89,
         'Distribution of scoring volatility — long right tail driven by low-usage players',
         fontsize=11, color=SUBTLE, ha='left')
ax.legend(fontsize=11, frameon=True, facecolor=CARD_BG, edgecolor=GRID, framealpha=0.95)
ax.grid(True, axis='y', alpha=0.4, zorder=1)
add_source_note(fig, y=-0.04)
save_chart(fig, '05_cv_distribution_histogram.png')

# ══════════════════════════════════════════════
# INTERACTIVE HTML DASHBOARD
#
# NNG-inspired design choices:
#   - Light warm-neutral background (#F5F5F0)
#   - Serif headline font for editorial authority
#   - Generous whitespace, clear section hierarchy
#   - Subtle card shadows (depth without distraction)
#   - Focus-visible outlines on interactive elements
#   - Descriptive labels, no ambiguous icons
#   - Table: sticky headers, thin scrollbar, sort arrows
#   - Accessible color contrast throughout
#   - Responsive grid collapses cleanly on mobile
# ══════════════════════════════════════════════
print("\nGenerating interactive HTML dashboard...")

scatter_data = agg[['firstName','lastName','team','PPG','StdDev','CV',
                     'gamesPlayed','avgMinutes','tier','maxPoints','minPoints']].copy()
scatter_data['PPG'] = scatter_data['PPG'].round(2)
scatter_data['StdDev'] = scatter_data['StdDev'].round(2)
scatter_data['CV'] = scatter_data['CV'].round(3)
scatter_data['avgMinutes'] = scatter_data['avgMinutes'].round(1)
scatter_data = scatter_data.fillna('')

records_json = scatter_data.to_json(orient='records')

tier_stats = agg.groupby('tier').agg(
    medianCV=('CV', 'median'),
    meanCV=('CV', 'mean'),
    count=('CV', 'count')
).reindex(tier_order)
tier_stats_json = tier_stats.reset_index().to_json(orient='records')

corr_ppg_cv = agg['PPG'].corr(agg['CV'])
corr_ppg_sd = agg['PPG'].corr(agg['StdDev'])

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NBA Scoring Volatility</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

  *, *::before, *::after {{ margin:0; padding:0; box-sizing:border-box; }}

  :root {{
    --bg:        #F5F5F0;
    --surface:   #FFFFFF;
    --border:    #E2E2DA;
    --border-subtle: #EDEDEA;
    --text:      #1A1A2E;
    --text-secondary: #5C5C72;
    --text-tertiary:  #8E8EA0;
    --accent:    #2563EB;
    --red:       #DC2626;
    --green:     #059669;
    --amber:     #B45309;
    --focus:     #2563EB33;
    --radius:    8px;
    --radius-lg: 12px;
    --shadow:    0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03);
    --shadow-md: 0 4px 12px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04);
  }}

  body {{
    background: var(--bg);
    color: var(--text);
    font-family: 'IBM Plex Sans', -apple-system, sans-serif;
    font-size: 14px;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
  }}

  .page {{ max-width: 1320px; margin: 0 auto; padding: 40px 32px 64px; }}

  header {{ margin-bottom: 36px; }}
  header h1 {{
    font-family: 'Source Serif 4', Georgia, serif;
    font-size: 32px; font-weight: 700; line-height: 1.2;
    color: var(--text); letter-spacing: -0.02em; margin-bottom: 8px;
  }}
  header p {{ font-size: 15px; color: var(--text-secondary); max-width: 640px; }}
  header .meta {{
    margin-top: 12px; font-size: 12px; color: var(--text-tertiary);
    letter-spacing: 0.02em; text-transform: uppercase;
  }}

  .kpi-row {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px; margin-bottom: 28px;
  }}
  .kpi {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius-lg); padding: 20px 24px; box-shadow: var(--shadow);
  }}
  .kpi .label {{
    font-size: 11px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.06em; color: var(--text-tertiary); margin-bottom: 6px;
  }}
  .kpi .value {{
    font-family: 'IBM Plex Mono', monospace; font-size: 28px;
    font-weight: 500; color: var(--text); line-height: 1.2;
  }}
  .kpi .detail {{ font-size: 12px; color: var(--text-secondary); margin-top: 4px; }}

  .filters {{
    display: flex; gap: 16px; flex-wrap: wrap; align-items: flex-end;
    margin-bottom: 28px; padding: 20px 24px;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius-lg); box-shadow: var(--shadow);
  }}
  .filter-group {{ display: flex; flex-direction: column; gap: 4px; }}
  .filter-group label {{
    font-size: 11px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.06em; color: var(--text-tertiary);
  }}
  .filter-group select, .filter-group input {{
    font-family: 'IBM Plex Sans', sans-serif; font-size: 13px;
    color: var(--text); background: var(--bg); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 8px 12px; outline: none;
    transition: border-color 0.15s, box-shadow 0.15s;
  }}
  .filter-group select:focus, .filter-group input:focus {{
    border-color: var(--accent); box-shadow: 0 0 0 3px var(--focus);
  }}
  .filter-group input[type="number"] {{ width: 80px; }}
  .filter-group input[type="text"] {{ width: 200px; }}

  .chart-grid {{
    display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 28px;
  }}
  .card {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius-lg); padding: 24px; box-shadow: var(--shadow);
  }}
  .card h2 {{
    font-family: 'IBM Plex Sans', sans-serif; font-size: 14px;
    font-weight: 600; color: var(--text); margin-bottom: 4px;
  }}
  .card .card-desc {{ font-size: 12px; color: var(--text-tertiary); margin-bottom: 16px; }}
  canvas {{ max-height: 340px; }}

  .table-card {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius-lg); box-shadow: var(--shadow); overflow: hidden;
  }}
  .table-header {{
    padding: 20px 24px 16px; border-bottom: 1px solid var(--border-subtle);
  }}
  .table-header h2 {{ font-size: 14px; font-weight: 600; color: var(--text); }}
  .table-header .count {{ font-size: 13px; color: var(--text-tertiary); font-weight: 400; }}
  .table-wrap {{ max-height: 560px; overflow-y: auto; }}
  .table-wrap::-webkit-scrollbar {{ width: 6px; }}
  .table-wrap::-webkit-scrollbar-track {{ background: transparent; }}
  .table-wrap::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}

  table {{ width: 100%; border-collapse: collapse; }}
  thead th {{
    position: sticky; top: 0; z-index: 2; background: var(--surface);
    text-align: left; padding: 10px 16px;
    font-size: 11px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.06em; color: var(--text-tertiary);
    border-bottom: 2px solid var(--border);
    cursor: pointer; user-select: none; white-space: nowrap;
    transition: color 0.15s;
  }}
  thead th:hover {{ color: var(--accent); }}
  thead th.sorted {{ color: var(--accent); }}
  thead th .sort-arrow {{ margin-left: 4px; font-size: 10px; }}
  tbody td {{
    padding: 10px 16px; font-size: 13px;
    border-bottom: 1px solid var(--border-subtle); white-space: nowrap;
  }}
  tbody tr:hover td {{ background: #F8F8F5; }}
  tbody tr:last-child td {{ border-bottom: none; }}
  .mono {{ font-family: 'IBM Plex Mono', monospace; font-size: 12.5px; }}
  .tier-pill {{
    display: inline-block; padding: 2px 10px; border-radius: 100px;
    font-size: 11px; font-weight: 600; letter-spacing: 0.02em;
  }}

  @media (max-width: 900px) {{
    .chart-grid {{ grid-template-columns: 1fr; }}
    .page {{ padding: 20px 16px 48px; }}
    header h1 {{ font-size: 24px; }}
  }}
  .kpi, .card, .table-card {{ transition: box-shadow 0.2s ease; }}
  .kpi:hover, .card:hover {{ box-shadow: var(--shadow-md); }}
</style>
</head>
<body>
<div class="page">

<header>
  <h1>NBA Scoring Volatility</h1>
  <p>How predictable are NBA scorers game-to-game? This dashboard measures volatility using Coefficient of Variation (CV)&thinsp;—&thinsp;the ratio of standard deviation to mean scoring. Lower CV means more consistent output.</p>
  <div class="meta">Oct 22 2024 &ndash; Mar 18 2026 &nbsp;&middot;&nbsp; Regular Season &amp; Playoffs &nbsp;&middot;&nbsp; Min {MIN_GAMES} games</div>
</header>

<div class="kpi-row" id="kpiRow"></div>

<div class="filters" role="search" aria-label="Filter players">
  <div class="filter-group">
    <label for="minPPG">Min PPG</label>
    <input type="number" id="minPPG" value="0" min="0" step="1">
  </div>
  <div class="filter-group">
    <label for="minGames">Min Games</label>
    <input type="number" id="minGames" value="{MIN_GAMES}" min="1" step="1">
  </div>
  <div class="filter-group">
    <label for="tierFilter">Tier</label>
    <select id="tierFilter">
      <option value="all">All Tiers</option>
      <option value="25+ PPG (Elite)">Elite (25+)</option>
      <option value="20-25 PPG (Star)">Star (20-25)</option>
      <option value="15-20 PPG (Starter)">Starter (15-20)</option>
      <option value="10-15 PPG (Rotation)">Rotation (10-15)</option>
      <option value="5-10 PPG (Bench)">Bench (5-10)</option>
      <option value="<5 PPG (Deep Bench)">Deep Bench (&lt;5)</option>
    </select>
  </div>
  <div class="filter-group">
    <label for="searchBox">Search</label>
    <input type="text" id="searchBox" placeholder="Player name or team...">
  </div>
</div>

<div class="chart-grid">
  <div class="card">
    <h2>Scoring Volume vs Volatility</h2>
    <p class="card-desc">Each dot is a player. As PPG rises, CV drops&thinsp;—&thinsp;stars are predictable.</p>
    <canvas id="scatterChart"></canvas>
  </div>
  <div class="card">
    <h2>Median Volatility by Tier</h2>
    <p class="card-desc">Clear staircase: elite scorers cluster near CV 0.35, bench players above 0.85.</p>
    <canvas id="tierChart"></canvas>
  </div>
  <div class="card">
    <h2>Absolute Point Swings vs PPG</h2>
    <p class="card-desc">Raw StdDev rises with PPG (r&thinsp;=&thinsp;{corr_ppg_sd:.2f})&thinsp;—&thinsp;bigger volume, bigger swings in raw terms.</p>
    <canvas id="stddevChart"></canvas>
  </div>
  <div class="card">
    <h2>CV Distribution</h2>
    <p class="card-desc">Right-skewed: most players below CV 1.5, long tail from low-usage players.</p>
    <canvas id="histChart"></canvas>
  </div>
</div>

<div class="table-card">
  <div class="table-header">
    <h2>All Players <span class="count" id="tableCount"></span></h2>
  </div>
  <div class="table-wrap">
    <table id="playerTable">
      <thead>
        <tr>
          <th data-col="name">Player</th>
          <th data-col="team">Team</th>
          <th data-col="PPG">PPG</th>
          <th data-col="StdDev">StdDev</th>
          <th data-col="CV">CV</th>
          <th data-col="gamesPlayed">GP</th>
          <th data-col="avgMinutes">MPG</th>
          <th data-col="tier">Tier</th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>
</div>

</div>

<script>
const ALL_DATA = {records_json};
const TIER_STATS = {tier_stats_json};

const TIER_COLORS = {{
  '25+ PPG (Elite)':      '#B45309',
  '20-25 PPG (Star)':     '#DC2626',
  '15-20 PPG (Starter)':  '#2563EB',
  '10-15 PPG (Rotation)': '#059669',
  '5-10 PPG (Bench)':     '#7C7C98',
  '<5 PPG (Deep Bench)':  '#B8B8CC',
}};
const TIER_BG = {{
  '25+ PPG (Elite)':      '#FEF3C7',
  '20-25 PPG (Star)':     '#FEE2E2',
  '15-20 PPG (Starter)':  '#DBEAFE',
  '10-15 PPG (Rotation)': '#D1FAE5',
  '5-10 PPG (Bench)':     '#F0F0F4',
  '<5 PPG (Deep Bench)':  '#F5F5FA',
}};

ALL_DATA.forEach(d => {{ d.name = d.firstName + ' ' + d.lastName; }});

Chart.defaults.font.family = "'IBM Plex Sans', sans-serif";
Chart.defaults.font.size = 11;
Chart.defaults.color = '#5C5C72';
Chart.defaults.plugins.legend.labels.boxWidth = 10;
Chart.defaults.plugins.legend.labels.padding = 14;
Chart.defaults.plugins.tooltip.backgroundColor = '#1A1A2E';
Chart.defaults.plugins.tooltip.cornerRadius = 6;
Chart.defaults.plugins.tooltip.titleFont = {{ weight: '600' }};
Chart.defaults.plugins.tooltip.padding = 10;

let sortCol = 'PPG', sortAsc = false;

function getFiltered() {{
  const minPPG = parseFloat(document.getElementById('minPPG').value) || 0;
  const minGP  = parseInt(document.getElementById('minGames').value) || 1;
  const tier   = document.getElementById('tierFilter').value;
  const search = document.getElementById('searchBox').value.toLowerCase();
  return ALL_DATA.filter(d =>
    d.PPG >= minPPG &&
    d.gamesPlayed >= minGP &&
    (tier === 'all' || d.tier === tier) &&
    (!search || d.name.toLowerCase().includes(search) || (d.team||'').toLowerCase().includes(search))
  );
}}

function updateKPIs(data) {{
  const n = data.length;
  if (!n) {{
    document.getElementById('kpiRow').innerHTML = '<div class="kpi"><div class="label">No players match filters</div></div>';
    return;
  }}
  const avgCV = (data.reduce((s,d) => s + d.CV, 0) / n).toFixed(2);
  const topScorer = data.reduce((m,d) => d.PPG > m.PPG ? d : m, data[0]);
  const mostConsistent = data.reduce((m,d) => d.CV < m.CV ? d : m, data[0]);
  const mostVolatile   = data.reduce((m,d) => d.CV > m.CV ? d : m, data[0]);

  document.getElementById('kpiRow').innerHTML = `
    <div class="kpi">
      <div class="label">Players</div>
      <div class="value">${{n}}</div>
      <div class="detail">matching current filters</div>
    </div>
    <div class="kpi">
      <div class="label">Avg Volatility</div>
      <div class="value">${{avgCV}}</div>
      <div class="detail">mean CV across filtered set</div>
    </div>
    <div class="kpi">
      <div class="label">Top Scorer</div>
      <div class="value" style="font-size:20px">${{topScorer.name}}</div>
      <div class="detail">${{topScorer.PPG.toFixed(1)}} ppg &middot; ${{topScorer.team}}</div>
    </div>
    <div class="kpi">
      <div class="label">Most Consistent</div>
      <div class="value" style="font-size:20px">${{mostConsistent.name}}</div>
      <div class="detail">CV ${{mostConsistent.CV.toFixed(3)}} &middot; ${{mostConsistent.PPG.toFixed(1)}} ppg</div>
    </div>
    <div class="kpi">
      <div class="label">Most Volatile</div>
      <div class="value" style="font-size:20px">${{mostVolatile.name}}</div>
      <div class="detail">CV ${{mostVolatile.CV.toFixed(3)}} &middot; ${{mostVolatile.PPG.toFixed(1)}} ppg</div>
    </div>
  `;
}}

function renderTable(data) {{
  const sorted = [...data].sort((a,b) => {{
    let va = a[sortCol], vb = b[sortCol];
    if (typeof va === 'string') {{ va = (va||'').toLowerCase(); vb = (vb||'').toLowerCase(); }}
    if (va < vb) return sortAsc ? -1 : 1;
    if (va > vb) return sortAsc ? 1 : -1;
    return 0;
  }});

  const tbody = document.querySelector('#playerTable tbody');
  tbody.innerHTML = sorted.map(d => `
    <tr>
      <td style="font-weight:500">${{d.name}}</td>
      <td>${{d.team || '\u2014'}}</td>
      <td class="mono">${{d.PPG.toFixed(1)}}</td>
      <td class="mono">${{d.StdDev.toFixed(1)}}</td>
      <td class="mono" style="font-weight:500">${{d.CV.toFixed(3)}}</td>
      <td class="mono">${{d.gamesPlayed}}</td>
      <td class="mono">${{d.avgMinutes}}</td>
      <td><span class="tier-pill" style="background:${{TIER_BG[d.tier]||'#F5F5FA'}};color:${{TIER_COLORS[d.tier]||'#7C7C98'}}">${{d.tier.split(' (')[0]}}</span></td>
    </tr>
  `).join('');

  document.getElementById('tableCount').textContent = '\u00b7 ' + data.length + ' players';

  document.querySelectorAll('#playerTable th').forEach(th => {{
    const arrow = th.querySelector('.sort-arrow');
    if (arrow) arrow.remove();
    th.classList.remove('sorted');
    if (th.dataset.col === sortCol) {{
      th.classList.add('sorted');
      const span = document.createElement('span');
      span.className = 'sort-arrow';
      span.textContent = sortAsc ? '\u2191' : '\u2193';
      th.appendChild(span);
    }}
  }});
}}

let scatterChart, tierChart, stddevChart, histChart;
const GRID_OPTS = {{ color: '#E8E8F0', lineWidth: 0.6 }};
const TICK_OPTS = {{ color: '#8E8EA0', font: {{ size: 10 }} }};

function buildCharts(data) {{
  if (!data.length) return;

  // ── Compute dynamic axis bounds from filtered data ──
  const ppgs = data.map(d => d.PPG);
  const cvs  = data.map(d => d.CV);
  const sds  = data.map(d => d.StdDev);

  const minPPGval = Math.min(...ppgs);
  const maxPPGval = Math.max(...ppgs);
  const minCVval  = Math.min(...cvs);
  const maxCVval  = Math.max(...cvs);
  const minSDval  = Math.min(...sds);
  const maxSDval  = Math.max(...sds);

  function padRange(lo, hi) {{
    const span = hi - lo || 1;
    return {{ min: Math.max(0, lo - span * 0.05), max: hi + span * 0.05 }};
  }}

  const ppgRange = padRange(minPPGval, maxPPGval);
  const cvRange  = padRange(minCVval, maxCVval);
  const sdRange  = padRange(minSDval, maxSDval);

  // 1. PPG vs CV
  const scatterDs = Object.keys(TIER_COLORS).map(tier => ({{
    label: tier.split(' (')[0],
    data: data.filter(d => d.tier === tier).map(d => ({{ x: d.PPG, y: d.CV, name: d.name, team: d.team, gp: d.gamesPlayed }})),
    backgroundColor: TIER_COLORS[tier] + '88',
    borderColor: TIER_COLORS[tier],
    borderWidth: 0.5,
    pointRadius: 4,
    pointHoverRadius: 7,
    pointHoverBorderWidth: 2,
  }}));

  if (scatterChart) scatterChart.destroy();
  scatterChart = new Chart(document.getElementById('scatterChart'), {{
    type: 'scatter',
    data: {{ datasets: scatterDs }},
    options: {{
      responsive: true, maintainAspectRatio: true,
      animation: {{ duration: 300 }},
      plugins: {{
        legend: {{ position: 'top' }},
        tooltip: {{ callbacks: {{
          label: ctx => `${{ctx.raw.name}} (${{ctx.raw.team}}) \u2014 ${{ctx.raw.x.toFixed(1)}} PPG, CV ${{ctx.raw.y.toFixed(3)}} (${{ctx.raw.gp}} gm)`
        }} }}
      }},
      scales: {{
        x: {{ title: {{ display:true, text:'Points Per Game', color:'#5C5C72' }}, grid: GRID_OPTS, ticks: TICK_OPTS, min: ppgRange.min, max: ppgRange.max }},
        y: {{ title: {{ display:true, text:'Coefficient of Variation', color:'#5C5C72' }}, grid: GRID_OPTS, ticks: TICK_OPTS, min: cvRange.min, max: cvRange.max }}
      }}
    }}
  }});

  // 2. Tier bar — recompute medians from filtered data
  const tierOrder = ['25+ PPG (Elite)', '20-25 PPG (Star)', '15-20 PPG (Starter)',
                     '10-15 PPG (Rotation)', '5-10 PPG (Bench)', '<5 PPG (Deep Bench)'];
  const filteredTierStats = tierOrder.map(tier => {{
    const vals = data.filter(d => d.tier === tier).map(d => d.CV).sort((a,b) => a - b);
    const n = vals.length;
    const median = n === 0 ? 0 : n % 2 === 1 ? vals[Math.floor(n/2)] : (vals[n/2-1] + vals[n/2]) / 2;
    return {{ tier, median, count: n }};
  }}).filter(t => t.count > 0);

  if (tierChart) tierChart.destroy();
  tierChart = new Chart(document.getElementById('tierChart'), {{
    type: 'bar',
    data: {{
      labels: filteredTierStats.map(t => t.tier.split(' (')[0]),
      datasets: [{{
        label: 'Median CV',
        data: filteredTierStats.map(t => t.median),
        backgroundColor: filteredTierStats.map(t => TIER_COLORS[t.tier] + '55'),
        borderColor: filteredTierStats.map(t => TIER_COLORS[t.tier]),
        borderWidth: 1.5, borderRadius: 4, barPercentage: 0.65,
      }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: true,
      animation: {{ duration: 300 }},
      plugins: {{ legend: {{ display: false }},
        tooltip: {{ callbacks: {{ label: ctx => `Median CV: ${{ctx.parsed.y.toFixed(3)}} (${{filteredTierStats[ctx.dataIndex].count}} players)` }} }}
      }},
      scales: {{
        x: {{ grid: {{ display: false }}, ticks: {{ ...TICK_OPTS, font: {{ size: 10 }} }} }},
        y: {{ title: {{ display:true, text:'Median CV', color:'#5C5C72' }}, grid: GRID_OPTS, ticks: TICK_OPTS, beginAtZero: true }}
      }}
    }}
  }});

  // 3. StdDev vs PPG
  if (stddevChart) stddevChart.destroy();
  stddevChart = new Chart(document.getElementById('stddevChart'), {{
    type: 'scatter',
    data: {{ datasets: [{{
      label: 'Players',
      data: data.map(d => ({{ x: d.PPG, y: d.StdDev, name: d.name }})),
      backgroundColor: '#2563EB44', borderColor: '#2563EB88',
      borderWidth: 0.5, pointRadius: 3, pointHoverRadius: 6,
    }}] }},
    options: {{
      responsive: true, maintainAspectRatio: true,
      animation: {{ duration: 300 }},
      plugins: {{ legend: {{ display: false }},
        tooltip: {{ callbacks: {{ label: ctx => `${{ctx.raw.name}}: ${{ctx.raw.x.toFixed(1)}} PPG, \u03c3 ${{ctx.raw.y.toFixed(1)}}` }} }}
      }},
      scales: {{
        x: {{ title: {{ display:true, text:'Points Per Game', color:'#5C5C72' }}, grid: GRID_OPTS, ticks: TICK_OPTS, min: ppgRange.min, max: ppgRange.max }},
        y: {{ title: {{ display:true, text:'Std Deviation', color:'#5C5C72' }}, grid: GRID_OPTS, ticks: TICK_OPTS, min: sdRange.min, max: sdRange.max }}
      }}
    }}
  }});

  // 4. Histogram — dynamic bins based on filtered CV range
  const cvMin = Math.floor(minCVval * 10) / 10;
  const cvMax = Math.min(Math.ceil(maxCVval * 10) / 10, 3);
  const bins = Math.min(40, Math.max(10, Math.round((cvMax - cvMin) / 0.05)));
  const step = (cvMax - cvMin) / bins || 0.075;
  const counts = new Array(bins).fill(0);
  data.forEach(d => {{
    const clamped = Math.min(d.CV, cvMax - 0.0001);
    const idx = Math.min(Math.floor((clamped - cvMin) / step), bins - 1);
    if (idx >= 0) counts[idx]++;
  }});

  if (histChart) histChart.destroy();
  histChart = new Chart(document.getElementById('histChart'), {{
    type: 'bar',
    data: {{
      labels: counts.map((_, i) => (cvMin + i * step).toFixed(2)),
      datasets: [{{
        label: 'Players', data: counts,
        backgroundColor: '#2563EB44', borderColor: '#2563EB88',
        borderWidth: 1, borderRadius: 2, barPercentage: 1.0, categoryPercentage: 1.0,
      }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: true,
      animation: {{ duration: 300 }},
      plugins: {{ legend: {{ display: false }} }},
      scales: {{
        x: {{ title: {{ display:true, text:'CV (binned)', color:'#5C5C72' }}, grid: {{ display:false }}, ticks: {{ ...TICK_OPTS, maxTicksLimit: 12 }} }},
        y: {{ title: {{ display:true, text:'Count', color:'#5C5C72' }}, grid: GRID_OPTS, ticks: TICK_OPTS }}
      }}
    }}
  }});
}}

function refresh() {{
  const data = getFiltered();
  updateKPIs(data);
  renderTable(data);
  buildCharts(data);
}}

document.querySelectorAll('.filters input, .filters select').forEach(el =>
  el.addEventListener('input', refresh));

document.querySelectorAll('#playerTable th').forEach(th => {{
  th.addEventListener('click', () => {{
    const col = th.dataset.col;
    if (sortCol === col) sortAsc = !sortAsc;
    else {{ sortCol = col; sortAsc = col === 'name' || col === 'team'; }}
    renderTable(getFiltered());
  }});
}});

refresh();
</script>
</body>
</html>""";

html_path = os.path.join(OUTPUT_DIR, 'scoring_volatility_dashboard.html')
with open(html_path, 'w') as f:
    f.write(html)
print(f"  Dashboard saved: {html_path}")

# ──────────────────────────────────────────────
# SUMMARY
# ──────────────────────────────────────────────
print(f"""
{'='*60}
  DONE! All outputs saved to:
  {OUTPUT_DIR}

  Files:
    - player_scoring_volatility.csv
    - 01_ppg_vs_volatility_scatter.png
    - 02_volatility_by_tier_boxplot.png
    - 03_consistent_vs_volatile.png
    - 04_stddev_vs_ppg_scatter.png
    - 05_cv_distribution_histogram.png
    - scoring_volatility_dashboard.html
{'='*60}
""")
