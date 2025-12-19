# %%

#Most Runs in IPL 2008-24
import pandas as pd
import plotly.express as px

# Load the CSV file
df = pd.read_csv("C:/Users/sudhe/OneDrive/Desktop/Social Web Analytics Group Project/ball_by_ball_data.csv")

# Filter for IPL matches (you can adjust this if needed)
ipl_df = df[df['series'].str.contains("Indian Premier League", na=False)]

# Group by batter and sum runs
batter_stats = (
    ipl_df.groupby("batter")["batruns"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
    .head(20)
)

# Create interactive bar chart with tooltips
fig = px.bar(
    batter_stats,
    x="batter",
    y="batruns",
    text="batruns",
    title="Top 20 Run Scorers - IPL 2008-24",
    labels={"batruns": "Total Runs", "batter": "Player"},
)

fig.update_traces(texttemplate='%{text}', hovertemplate='Player: %{x}<br>Runs: %{y}')
fig.update_layout(xaxis_tickangle=-45)

# Show the chart
fig.show()




# %%
#Season-wise Run Rate Analysis
import pandas as pd
import plotly.express as px

# Load the CSV file
df = pd.read_csv("C:/Users/sudhe/OneDrive/Desktop/Social Web Analytics Group Project/ball_by_ball_data.csv")

# Filter for valid entries
df = df[df['valid_ball'] == 1]

# Group by season and calculate total runs and total valid balls
season_stats = (
    df.groupby('year')
    .agg(total_runs=('totalRuns', 'sum'), total_balls=('valid_ball', 'sum'))
    .reset_index()
)

# Calculate run rate
season_stats['run_rate'] = season_stats['total_runs'] / (season_stats['total_balls'] / 6)

# Plot the line graph
fig = px.line(
    season_stats,
    x="year",
    y="run_rate",
    markers=True,
    title="Average Run Rate per Season (IPL)",
    labels={"year": "Season", "run_rate": "Run Rate (Runs per Over)"}
)

fig.update_traces(line=dict(width=3), marker=dict(size=8))
fig.update_layout(xaxis=dict(dtick=1))  # Show all years on x-axis
fig.show()
# %%

#Pace-Spin Distribution by Over
# Load the bowling type mapping (from your screenshot)
bowling_map = {
    'lf': 'pace', 'lm': 'pace', 'lbg': 'spin', 'lmf': 'pace',
    'rfm': 'pace', 'ob': 'spin', 'rm': 'pace', 'sla': 'spin',
    'rmf': 'pace', 'lfm': 'pace', 'rf': 'pace', 'lb': 'spin',
    'lws': 'spin', 'rm,ob,lb': 'spin', 'ob,lbg': 'spin',
    'ob,lb': 'spin', 'rm,ob': 'spin', 'sla,lws': 'spin'
}

# Clean and standardize bowling_style column
def classify_bowling_style(style_str):
    styles = str(style_str).split(',')
    types = set(bowling_map.get(s.strip(), 'unknown') for s in styles)
    return 'pace' if 'pace' in types else 'spin' if 'spin' in types else 'unknown'

df['bowling_type'] = df['bowling_style'].apply(classify_bowling_style)

# Filter only valid balls
df = df[df['valid_ball'] == 1]

# Group by over and bowling type
over_stats = (
    df.groupby(['over', 'bowling_type'])
    .size()
    .reset_index(name='deliveries')
)

# Total deliveries per over
total_per_over = over_stats.groupby('over')['deliveries'].sum().reset_index(name='total')

# Merge back to calculate %
over_stats = over_stats.merge(total_per_over, on='over')
over_stats['percent'] = (over_stats['deliveries'] / over_stats['total']) * 100

# Plot: Grouped bar chart
fig = px.bar(
    over_stats,
    x='over',
    y='percent',
    color='bowling_type',
    barmode='stack',
    text='percent',
    labels={'percent': '% of deliveries', 'over': 'Over Number', 'bowling_type': 'Bowling Type'},
    title='Bowling Type Distribution by Over (All Seasons)'
)

fig.update_layout(xaxis=dict(dtick=1), yaxis_title="% of Deliveries")
fig.update_traces(
    texttemplate='%{text:.1f}%',
    textposition='inside',
    hovertemplate='Over: %{x}<br>Type: %{legendgroup}<br>Percent: %{y:.0f}%'
)
fig.show()
# %%
# Over-wise Run Rate by Batting Team and Season

import plotly.graph_objects as go

# Filter valid deliveries
df = df[df['valid_ball'] == 1]

# Group by team, year, over
overwise_stats = (
    df.groupby(['batting_team', 'year', 'over'])
    .agg(total_runs=('totalRuns', 'sum'), balls=('valid_ball', 'sum'))
    .reset_index()
)
overwise_stats['run_rate'] = overwise_stats['total_runs'] / (overwise_stats['balls'] / 6)

# Unique teams and years
teams = sorted(df['batting_team'].dropna().unique())
years = sorted(df['year'].dropna().unique())

# Set default
default_team = 'Royal Challengers Bangalore'
default_year = 2016

# Create figure
fig = go.Figure()


# Add bar traces (one per team-year)
for team in teams:
    for year in years:
        subset = overwise_stats[(overwise_stats['batting_team'] == team) & (overwise_stats['year'] == year)]
        fig.add_trace(go.Bar(
            x=subset['over'],
            y=subset['run_rate'],
            name=f"{team} ({year})",
            visible=(team == default_team and year == default_year),
            hovertemplate='Over %{x}<br>Run Rate: %{y:.2f}<extra></extra>'
        ))

# Dropdown for teams (top)
team_buttons = []
for team in teams:
    vis = [(trace.name.startswith(team) and trace.name.endswith(f"({default_year})")) for trace in fig.data]
    team_buttons.append(dict(
        label=team,
        method='update',
        args=[
            {"visible": vis},
            {"title": f"<b>Run Rate by Over – {team} ({default_year})</b>"}
        ]
    ))

# Dropdown for years (below)
year_buttons = []
for year in years:
    vis = [(trace.name.endswith(f"({year})") and trace.name.startswith(default_team)) for trace in fig.data]
    year_buttons.append(dict(
        label=str(year),
        method='update',
        args=[
            {"visible": vis},
            {"title": f"<b>Run Rate by Over – {default_team} ({year})</b>"}
        ]
    ))

# Layout adjustments
fig.update_layout(
    updatemenus=[
        dict(
            buttons=team_buttons,
            direction="down",
            showactive=True,
            x=0.01, y=1.1,
            xanchor="left", yanchor="top"
        ),
        dict(
            buttons=year_buttons,
            direction="down",
            showactive=True,
            x=0.01, y=0.95,
            xanchor="left", yanchor="top"
        )
    ],
    title=f"<b>Run Rate by Over – {default_team} ({default_year})</b>",
    title_x=0.4,  # move title to the right
    xaxis_title="Over",
    yaxis_title="Run Rate",
    xaxis=dict(dtick=1),
    barmode='group',
    hovermode='x unified',
    height=600
)

fig.show()
# %%

# Wagon Wheel Analysis for a Batter
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Replace these with the batter and year you want to visualize
batter_input = "V Kohli"
year_input = 2024

df = pd.read_csv("C:/Users/sudhe/OneDrive/Desktop/Social Web Analytics Group Project/ball_by_ball_data.csv")

# --- FILTER DATA ---
df_batter = df[(df['batter'] == batter_input) & (df['year'] == year_input)]
df_batter = df_batter[df_batter['batruns'] > 0]
df_batter = df_batter.dropna(subset=['wagonZone'])

# --- COUNT RUNS BY WAGON ZONE ---
zone_runs = df_batter.groupby('wagonZone')['batruns'].sum().reindex(range(1, 9), fill_value=0)
zone_percent = (zone_runs / zone_runs.sum() * 100).round(1).values

# --- ANGLE ORDER BASED ON VISUAL MAPPING ---
# Zones ordered as per your desired clock-style layout
zone_order = [2, 1, 8, 7, 6, 5, 4, 3]
zone_percent_ordered = [zone_percent[i - 1] for i in zone_order]

# --- PLOT SETTINGS ---
angles = np.linspace(0, 2 * np.pi, 9)[:-1]  # 8 slices
radii = np.ones(8) * 10
colors = plt.cm.Blues(np.array(zone_percent_ordered) / 100)

fig, ax = plt.subplots(subplot_kw={'polar': True}, figsize=(5, 5), facecolor='black')
ax.set_facecolor('black')

# Plot the chart
bars = ax.bar(angles, radii, width=np.pi / 4, color=colors, edgecolor='white', align='edge')

# Add % labels
for angle, pct in zip(angles, zone_percent_ordered):
    ax.text(angle + np.pi / 8, 5, f'{int(pct)}', ha='center', va='center', color='black', fontsize=12)

# Final cleanup
ax.set_xticks([])
ax.set_yticks([])
ax.set_title(f"% of Runs by Wagon Zone – {batter_input} ({year_input})", color='white', pad=20)
plt.tight_layout()
plt.show()

# %%
