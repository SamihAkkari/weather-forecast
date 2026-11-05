import logging
import sys

from src.data.maintenance import thin_forecast_runs, purge_old_bronze

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    stream=sys.stdout,
    force=True,
)

if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    full = "--full-vacuum" in sys.argv
    try:
        thin_forecast_runs(dry_run=dry_run, full_vacuum=full)   # 1) thin first
        if not dry_run:
            purge_old_bronze(keep_days=3, full_vacuum=full)     # 2) then purge bronze
    except Exception:
        logging.getLogger("maintenance").exception("Maintenance failed")
        sys.exit(1)