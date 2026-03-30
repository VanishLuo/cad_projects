# User Guide

## Quick Start

1. Install the package from the release artifact.
2. Launch `license-management.exe`.
3. Import license records from JSON files.
4. Use main list search and feature search filters.

## Core Operations

- Add/Edit license record
- Batch import and dedup report review
- Start/Stop provider actions
- Cross-target compare and export

## Compare Text Behavior

- Compare is available in committed workspace only.
- Select one row: compares initial text vs current text for the same record.
- Select two rows: compares current license text from both targets.
- Diff dialog uses color highlights:
	- Yellow: changed lines
	- Red: removed lines
	- Green: added lines

## Edit License Behavior

- Edit License opens remote file text editor for the selected row.
- Header displays server identity values from target host:
	- Server Hostname
	- Server MAC
- Hostname and MAC text are selectable for copy.
- MAC value is normalized for display by removing ':' characters.
- Saving writes updated text back to remote license file and refreshes compare text data.

## Workspace Behavior

- Use Switch Workspace to toggle between staging and committed views.
- Staging allows add/import/check/delete and editing of table fields.
- Committed is read-only for table edits and is intended for compare/export/remote operations.

## Troubleshooting

- Validation errors: follow inline feedback and date format hints.
- Import failures: open import report and correct invalid payload fields.
- Search no results: reset filters and retry with broader terms.
