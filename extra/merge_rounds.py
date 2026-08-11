#!/usr/bin/env python3
"""Merge per-round worker results into {browser}/merged/{worker}.

For each browser (chrome, firefox, safari) and each worker found under its
round directories, concatenate result.log across rounds (in round order)
and copy the error_points.json from the last round the worker appears in.
logs/ and outputs/ subfolders are not copied. Existing files are never
modified; output goes to a new {browser}/merged/{worker} directory.
"""

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BROWSERS = ["chrome", "firefox", "safari"]
ROUND_ORDER = ["first", "second", "third", "fourth", "fifth", "sixth"]

ERROR_POINTS_NAME = {
    "chrome": "Chrome_error_points.json",
    "firefox": "Firefox_error_points.json",
    "safari": "Safari_error_points.json",
}


def find_workers(browser_dir: Path) -> dict[str, list[str]]:
    """Map worker name -> list of round names (in ROUND_ORDER) it appears in."""
    workers: dict[str, list[str]] = {}
    for round_name in ROUND_ORDER:
        round_dir = browser_dir / round_name
        if not round_dir.is_dir():
            continue
        for worker_dir in sorted(round_dir.iterdir()):
            if not worker_dir.is_dir():
                continue
            if not (worker_dir / "result.log").is_file():
                continue
            workers.setdefault(worker_dir.name, []).append(round_name)
    return workers


def merge_worker(browser: str, browser_dir: Path, worker: str, rounds: list[str]) -> None:
    out_dir = browser_dir / "merged" / worker
    out_dir.mkdir(parents=True, exist_ok=True)

    merged_log = out_dir / "result.log"
    with merged_log.open("w") as out_f:
        for round_name in rounds:
            log_path = browser_dir / round_name / worker / "result.log"
            with log_path.open("r") as in_f:
                shutil.copyfileobj(in_f, out_f)

    last_round = rounds[-1]
    error_points_name = ERROR_POINTS_NAME[browser]
    src_error_points = browser_dir / last_round / worker / error_points_name
    if src_error_points.is_file():
        shutil.copyfile(src_error_points, out_dir / error_points_name)

    print(f"{browser}/{worker}: merged {rounds} -> {out_dir}")


def main() -> None:
    for browser in BROWSERS:
        browser_dir = ROOT / browser
        if not browser_dir.is_dir():
            continue
        workers = find_workers(browser_dir)
        for worker, rounds in workers.items():
            merge_worker(browser, browser_dir, worker, rounds)


if __name__ == "__main__":
    main()
