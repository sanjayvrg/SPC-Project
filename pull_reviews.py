import requests
import time
import json
import statistics
from datetime import datetime, timezone

patch_dates = [
    "2025-06-12",
    "2025-06-17",
    "2025-06-24",
    "2025-07-15",
    "2025-07-17",
    "2025-08-05",
    "2025-08-26",
    "2025-08-29",
    "2025-09-02",
    "2025-09-04",
    "2025-09-16",
    "2025-10-23",
    "2025-11-04",
    "2025-11-18",
    "2025-12-02",
    "2025-12-04",
    "2026-01-22",
    "2026-02-03",
    "2026-02-10",
    "2026-03-17",
    "2026-03-25",
    "2026-04-14",
    "2026-04-28",
    "2026-05-06",
    "2026-05-19",
    "2026-05-29",
    "2026-06-09",
    "2026-06-16",
    "2026-07-07",
    "2026-08-12",
    "2026-08-17",
    "2026-08-25",
    "2026-09-22",
]

def date_to_unix(date_string):
    dt = datetime.strptime(date_string, "%Y-%m-%d")
    dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())

def get_reviews_page(cursor):
    url = "https://store.steampowered.com/appreviews/553850"
    params = {
        "json": 1,
        "filter": "recent",
        "language": "english",
        "num_per_page": 100,
        "cursor": cursor
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"request failed: {response.status_code}")
        return None

def get_reviews_until(cutoff_unix, max_pages=1500):
    cursor = "*"
    all_reviews = []
    pages_pulled = 0
    wait_time = 5

    while True:
        data = get_reviews_page(cursor)

        if data is None:
            print(f"request failed, waiting {wait_time} seconds before retrying...")
            time.sleep(wait_time)
            wait_time = min(wait_time * 2, 120)
            continue

        wait_time = 5

        reviews = data["reviews"]
        if not reviews:
            break

        all_reviews.extend(reviews)
        cursor = data["cursor"]
        pages_pulled += 1

        oldest_in_page = min(r["timestamp_created"] for r in reviews)

        if oldest_in_page < cutoff_unix:
            print(f"reached cutoff after {pages_pulled} pages")
            break

        if pages_pulled >= max_pages:
            print("hit max_pages safety limit before reaching cut off")
            break

        if pages_pulled % 50 == 0:
            print(f"... {pages_pulled} pages pulled so far, oldest so far: {oldest_in_page}")
            with open("reviews_checkpoint.json", "w") as f:
                json.dump(all_reviews, f)

        time.sleep(1)

    return all_reviews

def compute_defect_rates(all_reviews, patch_dates_unix):
    defect_rates = []
    for i in range(len(patch_dates_unix) - 1):
        window_start = patch_dates_unix[i]
        window_end = patch_dates_unix[i + 1]

        in_window = [r for r in all_reviews if window_start <= r["timestamp_created"] < window_end]

        if not in_window:
            continue

        thumbs_down = [r for r in in_window if not r["voted_up"]]
        rate = len(thumbs_down) / len(in_window)
        defect_rates.append(rate)

    return defect_rates

def iterative_3sigma(data):
    if len(data) < 2:
        print("not enough data points to run 3-sigma analysis")
        return None

    data = data.copy()

    while True:
        mean = statistics.mean(data)
        std_dev = statistics.stdev(data)
        ucl = mean + 3 * std_dev
        lcl = mean - 3 * std_dev
        print(f"mean: {mean}, ucl: {ucl}, lcl: {lcl}")

        outliers = [x for x in data if x > ucl or x < lcl]

        if not outliers:
            break

        data = [x for x in data if x <= ucl and x >= lcl]

    return data, ucl, lcl


if __name__ == "__main__":
    with open("reviews_checkpoint.json", "r") as f:
        reviews = json.load(f)

    print(f"loaded {len(reviews)} reviews from checkpoint")
    print(f"oldest review timestamp: {min(r['timestamp_created'] for r in reviews)}")

    patch_dates_unix = [date_to_unix(d) for d in patch_dates]
    rates = compute_defect_rates(reviews, patch_dates_unix)
    print(rates)

    result = iterative_3sigma(rates)
    if result:
        baseline, ucl, lcl = result
        print(f"baseline: {baseline}, ucl: {ucl}, lcl: {lcl}")