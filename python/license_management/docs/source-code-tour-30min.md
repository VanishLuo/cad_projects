# License Management 30-Minute Source Code Tour

This document is a practical 30-minute walkthrough for the current codebase.
Use it as a guided reading script from entry point to business flow.

## 0-5 min: Entry and Startup Strategy
- File: `src/license_management/__main__.py`
- Focus:
  - How CLI args are parsed (`--version`).
  - How GUI startup is delegated to `run_gui`.
  - How direct file execution in IDE is supported by appending `src` to `sys.path`.
  - How interpreter fallback works: if non-project interpreter cannot import PyQt5, relaunch with `.venv` Python.

## 5-12 min: GUI Shell and Dependency Wiring
- File: `src/license_management/gui/qt_app.py`
- Focus:
  - `MainWindow` owns widgets, user interactions, and rendering.
  - `build_context` wires repository + services + adapters + binder.
  - `run_gui` creates `QApplication`, opens window, and runs app loop.
- Key idea:
  - UI layer orchestrates and delegates; it does not implement core business rules.

## 12-18 min: GUI Action Binder (Main Orchestration Layer)
- File: `src/license_management/gui/dialog_flows.py`
- Focus:
  - `DialogFlowBinder` is the bridge from button actions to application services.
  - Main actions:
    - `add_or_edit`
    - `import_files`
    - `compare`
    - `start_stop`
    - `export_records`
- Key idea:
  - Feedback is normalized via `FeedbackMessage`, so UI behavior is consistent.

## 18-23 min: Application Services (Business Core)
- Files:
  - `src/license_management/application/import_pipeline.py`
  - `src/license_management/application/compare_service.py`
  - `src/license_management/application/expiration_engine.py`
- Focus:
  - Import pipeline: JSON loading, validation, deduplication, report generation.
  - Compare service: deterministic cross-target diff report by composite key.
  - Expiration engine: derive `active`, `expiring_soon`, `expired` from expiration date.

## 23-27 min: Domain Model and Repository Boundary
- Files:
  - `src/license_management/domain/models/license_record.py`
  - `src/license_management/domain/ports/license_repository.py`
  - `src/license_management/infrastructure/repositories/in_memory_license_repository.py`
- Focus:
  - Domain model is simple and explicit.
  - Repository is defined as a protocol boundary.
  - Infrastructure implementation can be replaced without changing app/domain logic.

## 27-30 min: Search/Filter and Validation Feedback
- Files:
  - `src/license_management/gui/view_model.py`
  - `src/license_management/gui/feature_search.py`
  - `src/license_management/gui/validation_feedback.py`
  - `src/license_management/gui/models.py`
- Focus:
  - Filter inputs -> row selection -> status/highlight mapping.
  - Form validation and conversion to domain record.
  - UI-level data model and feedback center.

## Four Main Call Chains
1. Startup chain:
   - `__main__.py` -> `qt_app.run_gui` -> `MainWindow(build_context())`
2. Search chain:
   - `MainWindow._apply_search` -> `FeatureSearchController.search` -> `MainListViewModel.search_and_filter` -> `ExpirationStateEngine.evaluate`
3. Import chain:
   - `MainWindow._import_json` -> `DialogFlowBinder.import_files` -> `ImportPipelineService.import_batch_files` -> `Repository.upsert`
4. Start/stop chain:
   - `MainWindow._start_stop` -> `DialogFlowBinder.start_stop` -> `FlexNetAdapter.start/stop` -> `SshCommandExecutor.run`

## Suggested Follow-up Reading (Optional)
- Read tests matching each chain to verify expected behavior end-to-end:
  - import/dedup
  - search/filter matrix
  - compare report determinism
  - adapter retry and rollback behaviors
