import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

BACKUP_RETENTION_DAYS = 7
BACKUP_DIR_NAME = "backups"


def daily_backup(db_path: Path) -> None:
    """Snapshot the SQLite DB once per day under backend/backups/. Keep the last 7."""
    if not db_path.exists():
        return

    backup_dir = db_path.parent / BACKUP_DIR_NAME
    backup_dir.mkdir(exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d")
    target = backup_dir / f"db.sqlite3.{stamp}.bak"
    if target.exists():
        return

    try:
        shutil.copy2(db_path, target)
        logger.info("DB backup created: %s", target.name)
    except OSError as e:
        logger.warning("DB backup failed: %s", e)
        return

    cutoff = datetime.now() - timedelta(days=BACKUP_RETENTION_DAYS)
    for old in backup_dir.glob("db.sqlite3.*.bak"):
        try:
            old_stamp = datetime.strptime(old.name.split(".")[2], "%Y%m%d")
        except (ValueError, IndexError):
            continue
        if old_stamp < cutoff:
            old.unlink(missing_ok=True)


def warn_if_no_users() -> None:
    """Log a loud warning if the user table is empty — usually means the DB was wiped."""
    from django.contrib.auth.models import User
    from django.db import OperationalError

    try:
        if User.objects.count() == 0:
            logger.warning(
                "No users in database. If you previously had accounts, the SQLite file may "
                "have been wiped or replaced. Check backend/backups/ for daily snapshots."
            )
    except OperationalError:
        # Auth tables not migrated yet — first-time setup, nothing to warn about.
        pass
