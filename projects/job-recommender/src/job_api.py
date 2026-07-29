import os
from dotenv import load_dotenv
from apify_client import ApifyClient

load_dotenv()

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
if not APIFY_API_TOKEN:
    raise ValueError("Missing APIFY_API_TOKEN. Please set it in your .env file.")

apify_client = ApifyClient(APIFY_API_TOKEN)


def fetch_linkedin_jobs(search_query: str, location: str = "India", rows: int = 60):
    """
    Fetch LinkedIn jobs based on search query and location using Apify actor.
    """
    run_input = {
        "title": search_query,
        "location": location,
        "rows": rows,
        "proxy": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"],
        },
    }

    try:
        run = apify_client.actor("BHzefUZlZRKWxkTck").call(run_input=run_input)
        jobs = list(apify_client.dataset(run["defaultDatasetId"]).iterate_items())
        return jobs
    except Exception as e:
        return {"error": f"Error fetching LinkedIn jobs: {e}"}
