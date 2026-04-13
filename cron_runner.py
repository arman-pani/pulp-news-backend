"""Standalone cron runner for Railway Cron Services.

Usage:
    python cron_runner.py --job scrape_and_notify
    python cron_runner.py --job cleanup

Railway Cron Service configuration
───────────────────────────────────
Service : cron-scrape
  Start command : python cron_runner.py --job scrape_and_notify
  Cron schedule : */15 * * * *   (every 15 minutes)

Service : cron-cleanup
  Start command : python cron_runner.py --job cleanup
  Cron schedule : 0 1 */5 * *   (every 5 days at 01:00 UTC)

Rotation state is stored entirely in Redis (REDIS_URL env var).
Each 15-minute tick advances through languages in the cycle:
    english → odia → bengali → english → …

Within each language, sources rotate round-robin independently:
    scraper:turn        — current language
    scraper:idx:english — next English source index (auto-wraps)
    scraper:idx:odia    — next Odia source index
    scraper:idx:bengali — next Bengali source index
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

    # Deferred imports — DB engine, Redis, and Firebase only initialise when
    # the process starts, so configuration errors surface immediately.
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
