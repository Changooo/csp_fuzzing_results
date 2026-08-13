#!/usr/bin/env python3
"""Merge per-worker (machine) results under {browser}/merged into a single
combined result for each browser.

Each worker (e.g. loki, odin, thor) owns a mostly disjoint CSP index range
(see role.json), so merging across workers means:
  - result.log: concatenate all workers' lines (ranges don't overlap)
  - {Browser}_error_points.json: merge the dicts keyed by CSP index. A few
    keys near range boundaries are tested by two workers; for those, the
    point lists are unioned together.

Reads only from {browser}/merged/{worker}/ (produced by merge_rounds.py) and
never modifies existing files. Output goes to a new {browser}/merged_all/
directory.
"""

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BROWSERS = ["chrome", "firefox", "safari"]

ERROR_POINTS_NAME = {
    "chrome": "Chrome_error_points.json",
    "firefox": "Firefox_error_points.json",
    "safari": "Safari_error_points.json",
}


def merge_browser(browser: str) -> None:
    browser_dir = ROOT / browser
    merged_dir = browser_dir / "merged"
    if not merged_dir.is_dir():
        return

    workers = sorted(
        w.name for w in merged_dir.iterdir()
        if w.is_dir() and (w / "result.log").is_file()
    )
    if not workers:
        return

    out_dir = browser_dir / "merged_all"
    out_dir.mkdir(parents=True, exist_ok=True)

    merged_log = out_dir / "result.log"
    with merged_log.open("w") as out_f:
        for worker in workers:
            log_path = merged_dir / worker / "result.log"
            with log_path.open("r") as in_f:
                shutil.copyfileobj(in_f, out_f)

    error_points_name = ERROR_POINTS_NAME[browser]
    combined_points: dict[str, list[int]] = {}
    for worker in workers:
        points_path = merged_dir / worker / error_points_name
        if not points_path.is_file():
            continue
        with points_path.open("r") as f:
            data = json.load(f)
        for key, points in data.items():
            if key in combined_points:
                combined_points[key] = sorted(set(combined_points[key]) | set(points))
            else:
                combined_points[key] = points

    sorted_points = {k: combined_points[k] for k in sorted(combined_points, key=int)}
    with (out_dir / error_points_name).open("w") as f:
        json.dump(sorted_points, f, indent=4)

    print(f"{browser}: merged {workers} -> {out_dir}")


def main() -> None:
    for browser in BROWSERS:
        merge_browser(browser)


if __name__ == "__main__":
    main()
