# Changelog

All notable changes to this project will be documented in this file.

## [3.0.5] - 2025-01-27

### Changed

- Removed log truncation - full log content is now displayed instead of being limited to 2000 lines

## [3.0.4] - 2025-01-27

### Fixed

- Frontend assets are now bundled with the Python package, so `skedulord serve` works out of the box after pip install

## [3.0.3] - 2025-01-27

- Broken release (frontend not bundled)

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
