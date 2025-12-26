import datetime as dt
import random
import uuid
from pathlib import Path

from skedulord.auth import hash_password
from skedulord.common import job_name_path
from skedulord.db import fetch_user, insert_run, insert_user, update_user_password


def _isoformat(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).isoformat(timespec="seconds")


def _write_log(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    random.seed(42)
    now = dt.datetime.now(dt.timezone.utc)

    admin_hash = hash_password("admin")
    if fetch_user("admin"):
        update_user_password("admin", admin_hash)
    else:
        insert_user("admin", admin_hash)

    job_names = [
        "billing-rollup",
        "cache-warmup",
        "daily-ingest",
        "email-digest",
        "fraud-scan",
        "geo-sync",
        "image-resize",
        "inventory-reconcile",
        "log-pruner",
        "metric-rollup",
        "model-train",
        "notifications",
        "payments-export",
        "pipeline-backfill",
        "product-sync",
        "quality-gate",
        "recommend-refresh",
        "reporter",
        "search-index",
        "session-cleanup",
        "sla-check",
        "snapshotter",
        "support-export",
        "user-sync",
        "warehouse-load",
        "webhook-drain",
    ]

    for name in job_names:
        run_count = random.randint(12, 32)
        for _ in range(run_count):
            run_id = uuid.uuid4().hex
            status = random.choices(["success", "fail"], weights=[0.82, 0.18], k=1)[0]
            duration = random.randint(12, 2400)
            offset = random.randint(0, 60 * 60 * 24 * 30)
            start = now - dt.timedelta(seconds=offset)
            end = start + dt.timedelta(seconds=duration)
            start_text = _isoformat(start)
            end_text = _isoformat(end)

            command = f"python jobs/{'badpyjob.py' if status == 'fail' else 'pyjob.py'}"
            log_path = Path(job_name_path(name)) / f"{start.strftime('%Y-%m-%dT%H-%M-%S')}-{run_id[:6]}.txt"

            _write_log(
                log_path,
                [
                    f"job={name}",
                    f"run_id={run_id}",
                    f"status={status}",
                    f"duration={duration}s",
                    f"command={command}",
                    "Log output is synthetic for demo purposes.",
                ],
            )

            insert_run(
                run_id=run_id,
                name=name,
                command=command,
                status=status,
                start=start_text,
                end=end_text,
                logpath=str(log_path),
            )


if __name__ == "__main__":
    main()
