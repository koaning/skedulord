import datetime as dt
import random
import uuid
from pathlib import Path

from skedulord.auth import hash_password
from skedulord.common import job_name_path
from skedulord.db import fetch_user, insert_run, insert_user, update_user_password


def _isoformat(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).isoformat(timespec="seconds")


def _ts(base: dt.datetime, offset_seconds: int) -> str:
    """Generate a timestamp string with offset from base time."""
    t = base + dt.timedelta(seconds=offset_seconds)
    return t.strftime("[%Y-%m-%dT%H:%M:%SZ]")


def _generate_retry_block(start: dt.datetime, attempt: int, max_attempts: int, retry_delay: int, time_offset: int) -> list[str]:
    """Generate log lines for a retry attempt."""
    lines = []
    lines.append(f"{_ts(start, time_offset)} Attempt {attempt}/{max_attempts} failed")
    lines.append(f"{_ts(start, time_offset + 1)} Waiting {retry_delay}s before retry...")
    lines.append(f"{_ts(start, time_offset + retry_delay)} Retrying (attempt {attempt + 1}/{max_attempts})...")
    return lines


def _generate_data_job_logs(name: str, start: dt.datetime, duration: int, status: str) -> list[str]:
    """Generate logs for data processing jobs (daily-ingest, warehouse-load, pipeline-backfill)."""
    lines = []
    record_count = random.randint(10000, 500000)
    table_name = random.choice(["orders", "events", "transactions", "users", "products", "sessions"])

    lines.append(f"{_ts(start, 0)} Starting job: {name}")
    lines.append(f"{_ts(start, 0)} Connecting to source database...")
    lines.append(f"{_ts(start, 1)} Connection established (pool_size=5)")
    lines.append(f"{_ts(start, 2)} Fetching records from {table_name} table...")

    if status == "fail":
        max_attempts = random.randint(2, 3)
        retry_delay = random.randint(5, 15)
        attempt_duration = duration // max_attempts

        for attempt in range(1, max_attempts + 1):
            attempt_start = (attempt - 1) * attempt_duration
            fail_time = attempt_start + random.randint(3, min(attempt_duration - 5, 30))

            if attempt > 1:
                lines.append(f"{_ts(start, attempt_start)} Connecting to source database...")
                lines.append(f"{_ts(start, attempt_start + 1)} Connection established (pool_size=5)")
                lines.append(f"{_ts(start, attempt_start + 2)} Fetching records from {table_name} table...")

            lines.append(f"{_ts(start, fail_time)} ERROR: Connection timeout after {fail_time - attempt_start}s")
            lines.append(f"{_ts(start, fail_time)} Traceback (most recent call last):")
            lines.append(f'{_ts(start, fail_time)}   File "jobs/{name.replace("-", "_")}.py", line 42, in fetch_records')
            lines.append(f"{_ts(start, fail_time)}     cursor.execute(query)")
            lines.append(f"{_ts(start, fail_time)} TimeoutError: Connection to database timed out")

            if attempt < max_attempts:
                lines.extend(_generate_retry_block(start, attempt, max_attempts, retry_delay, fail_time))

        lines.append(f"{_ts(start, duration - 1)} Max retries ({max_attempts}) exceeded")
        lines.append(f"{_ts(start, duration)} Job failed after {duration}s")
    else:
        fetch_time = int(duration * 0.3)
        transform_time = int(duration * 0.6)
        lines.append(f"{_ts(start, fetch_time)} Retrieved {record_count:,} records")
        lines.append(f"{_ts(start, fetch_time + 1)} Validating data schema...")
        lines.append(f"{_ts(start, fetch_time + 2)} Schema validation passed (0 errors, 0 warnings)")
        lines.append(f"{_ts(start, fetch_time + 3)} Transforming records...")
        lines.append(f"{_ts(start, transform_time)} Transformation complete: {record_count:,} records processed")
        lines.append(f"{_ts(start, transform_time + 1)} Loading to destination...")
        lines.append(f"{_ts(start, duration - 1)} Load complete: {record_count:,} rows inserted, 0 errors")
        lines.append(f"{_ts(start, duration)} Job completed successfully in {duration}s")

    return lines


def _generate_sync_job_logs(name: str, start: dt.datetime, duration: int, status: str) -> list[str]:
    """Generate logs for sync jobs (geo-sync, user-sync, product-sync)."""
    lines = []
    source = random.choice(["api.external.com", "warehouse.internal", "s3://data-lake", "kafka://events"])
    sync_count = random.randint(500, 50000)
    conflicts = random.randint(0, 20)

    lines.append(f"{_ts(start, 0)} Starting job: {name}")
    lines.append(f"{_ts(start, 0)} Source: {source}")
    lines.append(f"{_ts(start, 0)} Destination: postgres://localhost/app")
    lines.append(f"{_ts(start, 1)} Fetching delta since last sync...")

    if status == "fail":
        max_attempts = random.randint(2, 3)
        retry_delay = random.randint(5, 15)
        attempt_duration = duration // max_attempts
        error = random.choice([
            "ConnectionRefusedError: Unable to reach source",
            "AuthenticationError: Invalid API credentials",
            "RateLimitError: Too many requests (429)",
        ])

        for attempt in range(1, max_attempts + 1):
            attempt_start = (attempt - 1) * attempt_duration
            fail_time = attempt_start + random.randint(2, min(attempt_duration - 5, 20))

            if attempt > 1:
                lines.append(f"{_ts(start, attempt_start)} Fetching delta since last sync...")

            lines.append(f"{_ts(start, fail_time)} ERROR: {error}")
            lines.append(f"{_ts(start, fail_time)} Traceback (most recent call last):")
            lines.append(f'{_ts(start, fail_time)}   File "jobs/{name.replace("-", "_")}.py", line 78, in sync')
            lines.append(f"{_ts(start, fail_time)}     response = client.fetch(endpoint)")
            lines.append(f"{_ts(start, fail_time)} {error.split(':')[0]}: {error.split(':')[1].strip()}")

            if attempt < max_attempts:
                lines.extend(_generate_retry_block(start, attempt, max_attempts, retry_delay, fail_time))

        lines.append(f"{_ts(start, duration - 1)} Max retries ({max_attempts}) exceeded")
        lines.append(f"{_ts(start, duration)} Job failed after {duration}s")
    else:
        mid = int(duration * 0.5)
        lines.append(f"{_ts(start, mid)} Found {sync_count:,} records to sync")
        lines.append(f"{_ts(start, mid + 1)} Syncing records...")
        for i in range(1, 4):
            pct = i * 33
            lines.append(f"{_ts(start, mid + i * 3)} Progress: {min(pct, 100)}% ({int(sync_count * pct / 100):,}/{sync_count:,})")
        lines.append(f"{_ts(start, duration - 2)} Resolving conflicts...")
        lines.append(f"{_ts(start, duration - 1)} Resolved {conflicts} conflicts (strategy: latest-wins)")
        lines.append(f"{_ts(start, duration)} Sync complete: {sync_count:,} records, {conflicts} conflicts resolved in {duration}s")

    return lines


def _generate_export_job_logs(name: str, start: dt.datetime, duration: int, status: str) -> list[str]:
    """Generate logs for export jobs (payments-export, support-export)."""
    lines = []
    row_count = random.randint(1000, 100000)
    file_size_mb = random.uniform(1.5, 50.0)
    export_format = random.choice(["CSV", "Parquet", "JSON"])

    lines.append(f"{_ts(start, 0)} Starting job: {name}")
    lines.append(f"{_ts(start, 0)} Export format: {export_format}")
    lines.append(f"{_ts(start, 1)} Querying data for export...")

    if status == "fail":
        max_attempts = random.randint(2, 3)
        retry_delay = random.randint(5, 15)
        attempt_duration = duration // max_attempts

        for attempt in range(1, max_attempts + 1):
            attempt_start = (attempt - 1) * attempt_duration
            fail_time = attempt_start + random.randint(2, min(attempt_duration - 5, 15))

            if attempt > 1:
                lines.append(f"{_ts(start, attempt_start)} Querying data for export...")

            lines.append(f"{_ts(start, fail_time)} ERROR: Disk quota exceeded")
            lines.append(f"{_ts(start, fail_time)} Traceback (most recent call last):")
            lines.append(f'{_ts(start, fail_time)}   File "jobs/{name.replace("-", "_")}.py", line 55, in write_export')
            lines.append(f"{_ts(start, fail_time)}     f.write(chunk)")
            lines.append(f"{_ts(start, fail_time)} OSError: [Errno 28] No space left on device")

            if attempt < max_attempts:
                lines.extend(_generate_retry_block(start, attempt, max_attempts, retry_delay, fail_time))

        lines.append(f"{_ts(start, duration - 1)} Max retries ({max_attempts}) exceeded")
        lines.append(f"{_ts(start, duration)} Job failed after {duration}s")
    else:
        query_time = int(duration * 0.4)
        lines.append(f"{_ts(start, query_time)} Query complete: {row_count:,} rows")
        lines.append(f"{_ts(start, query_time + 1)} Writing to /exports/{name}/{start.strftime('%Y%m%d')}.{export_format.lower()}...")
        lines.append(f"{_ts(start, duration - 2)} Compressing with gzip...")
        lines.append(f"{_ts(start, duration - 1)} Upload to s3://exports-bucket/{name}/")
        lines.append(f"{_ts(start, duration)} Export complete: {row_count:,} rows, {file_size_mb:.1f}MB in {duration}s")

    return lines


def _generate_maintenance_job_logs(name: str, start: dt.datetime, duration: int, status: str) -> list[str]:
    """Generate logs for maintenance jobs (log-pruner, session-cleanup, cache-warmup)."""
    lines = []

    lines.append(f"{_ts(start, 0)} Starting job: {name}")

    if "pruner" in name or "cleanup" in name:
        items = random.randint(100, 10000)
        space_mb = random.uniform(10, 500)
        lines.append(f"{_ts(start, 1)} Scanning for expired items...")
        lines.append(f"{_ts(start, int(duration * 0.3))} Found {items:,} items older than 30 days")
        if status == "fail":
            max_attempts = random.randint(2, 3)
            retry_delay = random.randint(5, 10)
            attempt_duration = int(duration * 0.7) // max_attempts

            for attempt in range(1, max_attempts + 1):
                attempt_start = int(duration * 0.3) + (attempt - 1) * attempt_duration
                fail_time = attempt_start + random.randint(2, max(3, attempt_duration - 5))

                if attempt > 1:
                    lines.append(f"{_ts(start, attempt_start)} Deleting expired items...")

                lines.append(f"{_ts(start, fail_time)} ERROR: Permission denied on /var/log/app/")

                if attempt < max_attempts:
                    lines.extend(_generate_retry_block(start, attempt, max_attempts, retry_delay, fail_time))

            lines.append(f"{_ts(start, duration - 1)} Max retries ({max_attempts}) exceeded")
            lines.append(f"{_ts(start, duration)} Job failed after {duration}s")
        else:
            lines.append(f"{_ts(start, int(duration * 0.5))} Deleting expired items...")
            lines.append(f"{_ts(start, duration - 1)} Deleted {items:,} items, freed {space_mb:.1f}MB")
            lines.append(f"{_ts(start, duration)} Cleanup complete in {duration}s")
    else:  # cache-warmup
        endpoints = random.randint(20, 100)
        lines.append(f"{_ts(start, 1)} Loading cache configuration...")
        lines.append(f"{_ts(start, 2)} Warming {endpoints} endpoints...")
        if status == "fail":
            max_attempts = random.randint(2, 3)
            retry_delay = random.randint(5, 10)
            attempt_duration = int(duration * 0.9) // max_attempts

            for attempt in range(1, max_attempts + 1):
                attempt_start = 3 + (attempt - 1) * attempt_duration
                fail_time = attempt_start + random.randint(2, max(3, attempt_duration - 5))

                if attempt > 1:
                    lines.append(f"{_ts(start, attempt_start)} Warming {endpoints} endpoints...")

                lines.append(f"{_ts(start, fail_time)} ERROR: Redis connection refused")

                if attempt < max_attempts:
                    lines.extend(_generate_retry_block(start, attempt, max_attempts, retry_delay, fail_time))

            lines.append(f"{_ts(start, duration - 1)} Max retries ({max_attempts}) exceeded")
            lines.append(f"{_ts(start, duration)} Job failed after {duration}s")
        else:
            lines.append(f"{_ts(start, int(duration * 0.5))} Progress: 50% ({endpoints // 2}/{endpoints})")
            lines.append(f"{_ts(start, duration - 1)} Cache hit ratio: 94.2%")
            lines.append(f"{_ts(start, duration)} Warmed {endpoints} endpoints in {duration}s")

    return lines


def _generate_ml_job_logs(name: str, start: dt.datetime, duration: int, status: str) -> list[str]:
    """Generate logs for ML jobs (model-train, recommend-refresh)."""
    lines = []
    epochs = random.randint(5, 20)
    samples = random.randint(10000, 1000000)

    lines.append(f"{_ts(start, 0)} Starting job: {name}")
    lines.append(f"{_ts(start, 1)} Loading training data...")
    lines.append(f"{_ts(start, 3)} Loaded {samples:,} samples")
    lines.append(f"{_ts(start, 4)} Initializing model...")

    if status == "fail":
        max_attempts = random.randint(2, 3)
        retry_delay = random.randint(10, 30)
        attempt_duration = duration // max_attempts

        for attempt in range(1, max_attempts + 1):
            attempt_start = (attempt - 1) * attempt_duration
            fail_epoch = random.randint(1, min(epochs, 3))
            fail_time = attempt_start + int(attempt_duration * fail_epoch / epochs)

            if attempt > 1:
                lines.append(f"{_ts(start, attempt_start)} Loading training data...")
                lines.append(f"{_ts(start, attempt_start + 2)} Loaded {samples:,} samples")
                lines.append(f"{_ts(start, attempt_start + 3)} Initializing model with new random seed...")

            # Show some epochs before failure
            epoch_time = attempt_start + 4
            for i in range(1, fail_epoch):
                loss = 0.8 / i + random.uniform(-0.05, 0.05)
                acc = min(0.5 + 0.04 * i + random.uniform(-0.02, 0.02), 0.98)
                lines.append(f"{_ts(start, epoch_time)} Epoch {i}/{epochs} - loss: {loss:.4f}, accuracy: {acc:.4f}")
                epoch_time += (attempt_duration - 10) // epochs

            lines.append(f"{_ts(start, fail_time)} Epoch {fail_epoch}/{epochs} - loss: NaN")
            lines.append(f"{_ts(start, fail_time)} ERROR: Training diverged - loss became NaN")
            lines.append(f"{_ts(start, fail_time)} Traceback (most recent call last):")
            lines.append(f'{_ts(start, fail_time)}   File "jobs/{name.replace("-", "_")}.py", line 112, in train')
            lines.append(f"{_ts(start, fail_time)}     loss.backward()")
            lines.append(f"{_ts(start, fail_time)} RuntimeError: Loss is NaN, stopping training")

            if attempt < max_attempts:
                lines.extend(_generate_retry_block(start, attempt, max_attempts, retry_delay, fail_time))

        lines.append(f"{_ts(start, duration - 1)} Max retries ({max_attempts}) exceeded")
        lines.append(f"{_ts(start, duration)} Job failed after {duration}s")
    else:
        epoch_duration = duration // epochs
        for i in range(1, epochs + 1):
            loss = 0.8 / i + random.uniform(-0.05, 0.05)
            acc = min(0.5 + 0.04 * i + random.uniform(-0.02, 0.02), 0.98)
            lines.append(f"{_ts(start, i * epoch_duration)} Epoch {i}/{epochs} - loss: {loss:.4f}, accuracy: {acc:.4f}")
        lines.append(f"{_ts(start, duration - 2)} Saving model checkpoint...")
        lines.append(f"{_ts(start, duration - 1)} Model saved to s3://models/{name}/latest.pt")
        lines.append(f"{_ts(start, duration)} Training complete: {epochs} epochs, final accuracy: {acc:.4f} in {duration}s")

    return lines


def _generate_alert_job_logs(name: str, start: dt.datetime, duration: int, status: str) -> list[str]:
    """Generate logs for alert/monitoring jobs (fraud-scan, sla-check, quality-gate)."""
    lines = []
    checks = random.randint(50, 500)
    issues = random.randint(0, 10)

    lines.append(f"{_ts(start, 0)} Starting job: {name}")
    lines.append(f"{_ts(start, 1)} Loading rule definitions...")
    lines.append(f"{_ts(start, 2)} Running {checks} checks...")

    if status == "fail":
        max_attempts = random.randint(2, 3)
        retry_delay = random.randint(5, 15)
        attempt_duration = duration // max_attempts

        for attempt in range(1, max_attempts + 1):
            attempt_start = (attempt - 1) * attempt_duration
            fail_time = attempt_start + random.randint(3, min(attempt_duration - 5, 20))

            if attempt > 1:
                lines.append(f"{_ts(start, attempt_start)} Running {checks} checks...")

            lines.append(f"{_ts(start, fail_time)} ERROR: Unable to fetch metrics from monitoring service")
            lines.append(f"{_ts(start, fail_time)} Traceback (most recent call last):")
            lines.append(f'{_ts(start, fail_time)}   File "jobs/{name.replace("-", "_")}.py", line 34, in check')
            lines.append(f"{_ts(start, fail_time)}     metrics = client.query(query)")
            lines.append(f"{_ts(start, fail_time)} ConnectionError: Failed to connect to metrics.internal:9090")

            if attempt < max_attempts:
                lines.extend(_generate_retry_block(start, attempt, max_attempts, retry_delay, fail_time))

        lines.append(f"{_ts(start, duration - 1)} Max retries ({max_attempts}) exceeded")
        lines.append(f"{_ts(start, duration)} Job failed after {duration}s")
    else:
        mid = int(duration * 0.6)
        passed = checks - issues
        lines.append(f"{_ts(start, mid)} Checks complete: {passed} passed, {issues} issues found")
        if issues > 0:
            for i in range(min(issues, 3)):
                severity = random.choice(["WARNING", "CRITICAL"])
                rule = random.choice(["latency_p99", "error_rate", "cpu_usage", "memory_pressure"])
                lines.append(f"{_ts(start, mid + i + 1)} [{severity}] {rule} exceeded threshold")
            lines.append(f"{_ts(start, duration - 2)} Sending alerts via PagerDuty...")
            lines.append(f"{_ts(start, duration - 1)} Notified on-call: team-platform")
        lines.append(f"{_ts(start, duration)} Scan complete: {checks} checks, {issues} issues in {duration}s")

    return lines


def _generate_generic_job_logs(name: str, start: dt.datetime, duration: int, status: str) -> list[str]:
    """Generate generic logs for jobs that don't fit other categories."""
    lines = []
    steps = random.randint(3, 8)

    lines.append(f"{_ts(start, 0)} Starting job: {name}")
    lines.append(f"{_ts(start, 1)} Initializing...")

    if status == "fail":
        max_attempts = random.randint(2, 3)
        retry_delay = random.randint(5, 15)
        attempt_duration = duration // max_attempts
        fail_step = random.randint(1, steps)

        for attempt in range(1, max_attempts + 1):
            attempt_start = (attempt - 1) * attempt_duration
            fail_time = attempt_start + int(attempt_duration * fail_step / steps)

            if attempt > 1:
                lines.append(f"{_ts(start, attempt_start)} Initializing...")

            for i in range(1, fail_step):
                step_time = attempt_start + int(attempt_duration * i / steps)
                lines.append(f"{_ts(start, step_time)} Step {i}/{steps} complete")

            lines.append(f"{_ts(start, fail_time)} Step {fail_step}/{steps} failed")
            lines.append(f"{_ts(start, fail_time)} ERROR: Unexpected error during execution")

            if attempt < max_attempts:
                lines.extend(_generate_retry_block(start, attempt, max_attempts, retry_delay, fail_time))

        lines.append(f"{_ts(start, duration - 1)} Max retries ({max_attempts}) exceeded")
        lines.append(f"{_ts(start, duration)} Job failed after {duration}s")
    else:
        for i in range(1, steps + 1):
            lines.append(f"{_ts(start, int(duration * i / steps))} Step {i}/{steps} complete")
        lines.append(f"{_ts(start, duration)} Job completed successfully in {duration}s")

    return lines


def _generate_log_lines(name: str, start: dt.datetime, duration: int, status: str) -> list[str]:
    """Generate realistic log lines based on job name."""
    if name in ("daily-ingest", "warehouse-load", "pipeline-backfill"):
        return _generate_data_job_logs(name, start, duration, status)
    elif name in ("geo-sync", "user-sync", "product-sync"):
        return _generate_sync_job_logs(name, start, duration, status)
    elif name in ("payments-export", "support-export"):
        return _generate_export_job_logs(name, start, duration, status)
    elif name in ("log-pruner", "session-cleanup", "cache-warmup"):
        return _generate_maintenance_job_logs(name, start, duration, status)
    elif name in ("model-train", "recommend-refresh"):
        return _generate_ml_job_logs(name, start, duration, status)
    elif name in ("fraud-scan", "sla-check", "quality-gate"):
        return _generate_alert_job_logs(name, start, duration, status)
    else:
        return _generate_generic_job_logs(name, start, duration, status)


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

            # Determine attempt count
            if status == "fail":
                # Failed runs exhausted retries (3-4 attempts)
                attempt = random.randint(3, 4)
            elif random.random() < 0.15:
                # ~15% of successful runs succeeded after retry
                attempt = random.randint(2, 3)
            else:
                # Most successful runs: first attempt
                attempt = 1

            command = f"python jobs/{'badpyjob.py' if status == 'fail' else 'pyjob.py'}"
            log_path = Path(job_name_path(name)) / f"{start.strftime('%Y-%m-%dT%H-%M-%S')}-{run_id[:6]}.txt"

            _write_log(
                log_path,
                _generate_log_lines(name, start, duration, status),
            )

            insert_run(
                run_id=run_id,
                name=name,
                command=command,
                status=status,
                start=start_text,
                end=end_text,
                logpath=str(log_path),
                attempt=attempt,
            )


if __name__ == "__main__":
    main()
