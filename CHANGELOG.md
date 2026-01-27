# Changelog

All notable changes to this project will be documented in this file.

## [3.0.2] - 2025-01-27

### Added

- New `skedulord rm` command to remove jobs from the schedule config file
- `--schedule/--no-schedule` flag on `add` and `rm` commands to update crontab automatically (default: on)

### Changed

- `skedulord schedule` now defaults to `schedule.yml` in the current directory (no argument required)

## [3.0.1] - 2025-01-27

### Added

- New `skedulord add` command to quickly add jobs to the schedule config file
  - Point to a script file and provide a cron expression
  - Auto-generates job name from filename (customizable with `--name`)
  - Validates file and config existence
  - Prevents duplicate job names

### Changed

- Removed outdated VITE_* warning comment from init template

## [3.0.0] - Previous Release

Initial 3.x release with FastAPI backend, React webapp, and SQLite storage.
