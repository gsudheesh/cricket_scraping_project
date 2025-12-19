import pandas as pd
import asyncio
import time

#  Path to your Excel file
excel_path = "../data/raw/match id.xlsx"

#  Folder to save JSON outputs
output_folder = "../data/raw/rem_matches"

#  Read the Excel file (sheet name optional if it's the first one)
df = pd.read_excel(excel_path)

#  Convert to list of tuples
final_matches = list(df[['series_id', 'match_id']].itertuples(index=False, name=None))

#  Import your existing main function from your scraper
from espn_scraper import main  # if it's in the same file, you don't need to re-import

#  Run the scraper
start = time.time()
asyncio.run(main(output_folder, final_matches))
print("Done! Time taken:", time.time() - start)

