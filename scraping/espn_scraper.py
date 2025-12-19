import nest_asyncio
import asyncio
import os
import json
from playwright.async_api import async_playwright

nest_asyncio.apply()

# Function to extract available innings from the dropdown
async def extract_innings_options(page, match_id):
    try:
        await page.goto(f"https://stats.espncricinfo.com/ci/engine/match/{match_id}.html", timeout=20000)
    except Exception as e:
        print(f"Page navigation failed: {e}")
        return None

    # Navigate to the "Commentary" tab
    try:
        await page.wait_for_selector("text='Commentary'", timeout=20000)
        await page.click("text='Commentary'")
    except Exception as e:
        print(f"Failed to find or click Commentary tab: {e}")
        return None

    # Click the dropdown to expand innings options
    try:
        dropdown_button_selector = ".ds-flex.ds-items-center.ds-border-ui-stroke.ds-h-6.ds-px-4.ds-w-full"
        await page.wait_for_selector(dropdown_button_selector, timeout=10000)
        await page.click(dropdown_button_selector)
        await asyncio.sleep(2)  # Allow time for the dropdown to expand

        # Get all the options available in the dropdown
        innings_options = await page.query_selector_all("ul.ds-flex li")
        innings_names = [await option.inner_text() for option in innings_options]
        innings_names = [innings.strip() for innings in innings_names]  # Remove any extra spaces
        return innings_names
    except Exception as e:
        print(f"Failed to determine the innings from the dropdown: {e}")
        return None

# Function to extract commentary for each selected innings
async def extract_commentary_for_innings(page, match_id, innings_name, inns_no):
    commentary_data = []  # To store extracted commentary data
    seen_urls = set()  # To keep track of the URLs that have already been requested
    next_inning_over = None  # To keep track of the next inning over

    # Reload the page
    await page.goto(f"https://stats.espncricinfo.com/ci/engine/match/{match_id}.html", timeout=15000)

    # Navigate to the "Commentary" tab again
    await page.wait_for_selector("text='Commentary'", timeout=20000)
    await page.click("text='Commentary'")

    # Click the dropdown to expand innings options again
    dropdown_button_selector = ".ds-flex.ds-items-center.ds-border-ui-stroke.ds-h-6.ds-px-4.ds-w-full"
    await page.wait_for_selector(dropdown_button_selector, timeout=10000)

    # Listen to all outgoing requests
    async def on_request(request):
        nonlocal commentary_data, seen_urls, next_inning_over
        if "https://hs-consumer-api.espncricinfo.com/v1/pages/match/comments" in request.url and f"inningNumber={inns_no}" in request.url and request.method == "GET":
            if request.url in seen_urls:
                return  # Skip processing if URL has already been seen

            seen_urls.add(request.url)  # Mark this URL as seen
            response = await request.response()
            if response and response.status == 200:
                try:
                    data = await response.json()
                    comments = data.get("comments", [])
                    commentary_data.extend(comments)
                    next_inning_over = data.get("nextInningOver")
                    print(f"Next inning over: {next_inning_over}")
                except Exception as e:
                    print(f"Failed to parse JSON from commentary request: {e}")

    page.on("request", on_request)

    await page.click(dropdown_button_selector)
    await asyncio.sleep(2)  # Allow time for the dropdown to expand

    # Select the specific innings from the dropdown
    innings_options = await page.query_selector_all("ul.ds-flex li")
    for option in innings_options:
        option_text = await option.inner_text()
        if innings_name in option_text:
            await option.click()
            print(f"Selected innings: {innings_name}")
            await asyncio.sleep(5)  # Allow time for the page to load the selected innings content
            break

    # Controlled scrolling to load all commentary until nextInningOver is None
    while True:
        # Scroll down incrementally, enough to load new content without overshooting
        await page.evaluate("window.scrollBy(0, 10000)")
        await asyncio.sleep(2)  # Allow time for the page to load more commentary
        if next_inning_over is None:
            break

    return commentary_data

# Function to extract the scorecard
async def extract_scorecard(page, match_id):
    scorecard_data = None  # To store extracted scorecard data

    # Function to handle requests and capture the scorecard data
    async def on_request(request):
        nonlocal scorecard_data  # Use nonlocal to modify the scorecard_data defined in the enclosing function
        if "https://hs-consumer-api.espncricinfo.com/v1/pages/match/scorecard" in request.url and request.method == "GET":
            response = await request.response()
            if response and response.status == 200:
                try:
                    scorecard_data = await response.json()
                except Exception as e:
                    print(f"Failed to parse JSON from scorecard request: {e}")

    # Listen to all outgoing requests
    page.on("request", on_request)

    # Open the match page with increased timeout to avoid issues
    try:
        await page.goto(f"https://stats.espncricinfo.com/ci/engine/match/{match_id}.html", timeout=15000)
    except Exception as e:
        print(f"Page navigation failed: {e}")
        return None

    # Navigate to the "Scorecard" tab
    try:
        await page.wait_for_selector("text='Scorecard'")  # Wait for up to 20 seconds for the element to be ready
        await page.click("text='Scorecard'")
    except Exception as e:
        print(f"Failed to find or click Scorecard tab: {e}")
        return None

    await asyncio.sleep(2)
    return scorecard_data

# Ensure the output folder exists
def ensure_folder_exists(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

# Main function to run both tasks
async def main(folder_path, final_matches):
    ensure_folder_exists(folder_path)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Set headless=True for better performance
        context = await browser.new_context(
            viewport={"width": 1920, "height": 5000}  # Increased viewport
        )
        page = await context.new_page()

        # Block popups and ads
        await page.route("/*", lambda route, request: route.abort() if "ads" in request.url or "popup" in request.url else route.continue_())
        await page.add_init_script("""
            window.open = () => {
                console.log('Popup attempt blocked');
                return null;
            };
        """)

        for series_id, match_id in final_matches:
            print(f"Processing series {series_id}, match {match_id}...")
            await page.goto(f"https://stats.espncricinfo.com/ci/engine/match/{match_id}.html", timeout=15000)
            url_string = "/".join(page.url.split("/")[:-1])

            # Extract the scorecard
            scorecard = await extract_scorecard(page, match_id)

            # Extract available innings
            innings_names = await extract_innings_options(page, match_id)
            print(f"Available innings: {innings_names}")

            comments_data = []
            if innings_names:
                for i in range(len(innings_names)):
                    # Extract commentary data for each innings
                    commentary_data = await extract_commentary_for_innings(page, match_id, innings_names[i], i + 1)
                    comments_data.append(commentary_data)

            # Combine extracted data
            combined_data = {
                "scorecard": scorecard,
                "commentary": [{"comments": comments} for comments in comments_data if comments]
            }

            # Save the combined data to a file
            filename = os.path.join(folder_path, f"match_{match_id}.json")
            with open(filename, "w") as outfile:
                json.dump(combined_data, outfile, indent=4)

            print(f"Data saved to {filename}")

        # Close the browser
        await browser.close()

import time
start = time.time()

folder_path = "../data/raw/rem_matches"
final_matches = [
    ['1449924', '1473440'],
]

asyncio.run(main(folder_path, final_matches))
print(time.time() - start)

