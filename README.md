# Cricket Scraping Project (ESPN Cricinfo → CSV → Analysis → Tableau)

This repo contains an end-to-end cricket analytics pipeline:
1) Scrape match scorecard + ball-by-ball commentary JSON from ESPN Cricinfo
2) Convert nested JSON into a clean, analysis-ready CSV
3) Run analysis scripts and build Tableau dashboards

## Repo structure
- `scraping/` – scraping scripts (Playwright) that save match JSON files
- `data/` – input files and generated datasets (raw + processed)
- `processing/` – JSON → DataFrame/CSV transformation
- `analysis/` – charts and insights using the processed CSV
- `tableau/` – Tableau workbooks and dashboard assets

## Data flow
`data/raw/match_ids.xlsx`
→ `scraping/` generates JSON files into `data/raw/rem_matches/`
→ `processing/` generates `data/processed/ball_by_ball_data.csv`
→ `analysis/` reads `data/processed/ball_by_ball_data.csv`
→ Tableau uses the processed CSV for dashboards

## How to run (high level)
- Run `scraping/espn_scraper_loop.py` to scrape matches listed in `data/raw/match_ids.xlsx`
- Run `processing/json_to_df.py` to build the ball-by-ball CSV
- Run `analysis/final_analysis.py` to generate charts

## Notes
- Some scripts may require updating file paths depending on where you run them from.
- Do not commit credentials or private tokens.
