"""Standalone cron runner for Railway Cron Services.

Usage:
    python cron_runner.py --job scrape_and_notify
    python cron_runner.py --job cleanup

Railway Cron Service configuration
───────────────────────────────────
Service : cron-scrape
  Start command : python cron_runner.py --job scrape_and_notify
  Cron schedule : 30 2,4,6,8,12,16 * * *
  (= 8am, 10am, 12pm, 2pm, 6pm, 10pm IST / 2:30, 4:30, 6:30, 8:30, 12:30, 16:30 UTC)

Service : cron-cleanup
  Start command : python cron_runner.py --job cleanup
  Cron schedule : 0 1 */5 * *
  (= every 5 days at 01:00 UTC)
"""

from __future__ import annotations

import argparse
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger("cron_runner")


def main() -> None:
    parser = argparse.ArgumentParser(description="Railway cron job runner")
    parser.add_argument(
        "--job",
        required=True,
        choices=["scrape_and_notify", "cleanup"],
        help="The job to run.",
    )
    args = parser.parse_args()

    # Deferred imports — DB engine and Firebase only initialise when the process starts.
    from app.core.config import get_settings
    from app.db import session_scope
    from app.services.jobs import run_cleanup_job, run_scrape_and_notify_job

    settings = get_settings()

    try:
        settings.validate_runtime_configuration()
    except ValueError as exc:
        logger.critical("Configuration error: %s", exc)
        sys.exit(1)

    job_registry = {
        "scrape_and_notify": run_scrape_and_notify_job,
        "cleanup": run_cleanup_job,
    }

    job_fn = job_registry[args.job]
    logger.info("Starting job: %s", args.job)

    try:
        with session_scope() as session:
            result = job_fn(session)
        logger.info("Job '%s' completed: %s", args.job, result)
    except Exception:
        logger.exception("Job '%s' failed", args.job)
        sys.exit(1)


if __name__ == "__main__":
    main()
