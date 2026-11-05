import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from logging.handlers import RotatingFileHandler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

ROOT = Path(__file__).resolve().parent.parent   # project root
log = logging.getLogger("scheduler")


def launch(module: str, timeout_s: int):
    """Run a script as a separate process, so a crash can never kill the scheduler."""
    log.info("Starting %s", module)
    try:
        result = subprocess.run([sys.executable, "-m", module], cwd=ROOT, timeout=timeout_s)
        log.info("%s finished (exit code %s)", module, result.returncode)
    except subprocess.TimeoutExpired:
        log.error("%s killed after %s seconds (timeout)", module, timeout_s)


def main():
    # logging.basicConfig(
    #     level=logging.INFO,
    #     format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    #     stream=sys.stdout,
    # )

    # handler = RotatingFileHandler(
    #     "/app/logs/app.log",
    #     maxBytes=5 * 1024 * 1024,  # 5 MB
    #     backupCount=5,
    # )

    # logging.basicConfig(
    #     level=logging.INFO,
    #     format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    #     handlers=[
    #         logging.StreamHandler(sys.stdout),
    #         handler,
    #     ],
    #     force = True
    # )
    logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    stream=sys.stdout,
    force=True,
)

    test_mode = os.getenv("SCHEDULER_TEST") == "1"
    obs_every = "*/1" if test_mode else "*/10"    # minutes
    fc_every = "*/2" if test_mode else "*/15"
    log.info("Test mode: %s | observations every %s min | forecast every %s min",
             test_mode, obs_every, fc_every)

    scheduler = BlockingScheduler(timezone="UTC")
    now = datetime.now(timezone.utc)

    scheduler.add_job(
        launch, CronTrigger(minute=obs_every),
        args=["scripts.ingest_observations", 1800],
        id="observations", max_instances=1, coalesce=True, next_run_time=now,
    )
    scheduler.add_job(
        launch, CronTrigger(minute=fc_every),
        args=["scripts.ingest_forecasts", 3600],
        id="forecast", max_instances=1, coalesce=True, next_run_time=now,
    )
    scheduler.add_job(
        launch, CronTrigger(hour=3, minute=30),          # 03:30 UTC = 04:30/05:30 Paris
        args=["scripts.maintenance", 1800],
        id="maintenance", max_instances=1, coalesce=True,
    )    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    main()