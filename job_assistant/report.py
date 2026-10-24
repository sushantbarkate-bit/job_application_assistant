from pathlib import Path
from datetime import date
import csv
from .storage import Store

def daily_report(store: Store, report_dir: str):
    # Includes jobs found today and jobs whose status changed today (e.g. approved).
    rows = store.rows(since=date.today().isoformat())
    out = Path(report_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"applications-{date.today().isoformat()}.csv"
    headers = ["job_id","title","company","location","url","score","status","created_at","notes","updated_at"]
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    counts = {}
    for row in rows:
        counts[row[6]] = counts.get(row[6], 0) + 1
    return path, counts
