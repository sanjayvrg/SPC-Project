import requests
import statistics
from datetime import datetime, timezone

patch_dates = [
    "2024-02-08",  # launch
    "2024-02-14",
    "2024-02-22",
    "2024-03-06",
    "2024-03-20",
    "2024-04-02",
    "2024-04-29",  # major balance patch, well known nerf controversy
    "2024-05-14",
    "2024-06-13",
    "2024-07-04",
    "2024-08-06",
    "2024-08-20",  # start of "60-day plan"
    "2024-09-17",
    "2024-10-15",
    "2024-11-05",
    "2024-12-13",
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
        "cursor": cursor  # fixed: use the actual param, not hardcoded "*"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"request failed: {response.status_code}")
        return None

def get_all_reviews(max_pages=5):
    cursor = "*"
    all_reviews = []
    pages_pulled = 0

    while True:
        data = get_reviews_page(cursor)
        reviews = data["reviews"]

        if not reviews:
            break

        all_reviews.extend(reviews)
        cursor = data["cursor"]
        pages_pulled += 1

        if pages_pulled >= max_pages:
            break

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
    
    mean = statistics.mean(data)
    std_dev = statistics.stdev(data)
    ucl = mean + 3 * std_dev
    lcl = mean - 3 * std_dev
    print(f"mean: {mean}, ucl: {ucl}, lcl: {lcl}")



if __name__ == "__main__":
    reviews = get_all_reviews(max_pages = 20)

    fake_dates = ["2026-09-20", "2026-09-21", "2026-09-22", "2026-09-23", "2026-09-24"]
    fake_dates_unix = [date_to_unix(d) for d in fake_dates]

    rates = compute_defect_rates(reviews, fake_dates_unix)
    print(rates)

    iterative_3sigma(rates)
