# Release 0.1.0

Release Date: 2026-03-20

## Features

- Completed GUI interaction integration (M06).
- Added testing and quality closure suites (M07).
- Added packaging and operations baseline utilities (M08/M09).

## Fixes

- Stabilized import report behavior and compare consistency.
- Hardened branch workflow with commit safety guards.

## Post-release Maintenance Updates (2026-03-30)

- Updated Compare Text flow to support current text compare for two selected records and initial-vs-current compare for one selected record.
- Added color-highlighted text compare dialog with line-level change visualization.
- Updated Edit License dialog to show server hostname and normalized server MAC values with selectable copy behavior.
- Unified workspace action naming from `reset_data` to `switch_workspace` for clearer semantics.
- Aligned static typing and lint compliance for GUI dialogs and main window event handlers.

## Known Issues

- SQLite resource warning may appear in test runtime logs.
- Windows-only packaging validation still requires target machine confirmation.
