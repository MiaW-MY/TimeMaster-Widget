# Time Master Requirements

## 1. Product Goal

`TimeMaster-Widget` is a floating desktop countdown widget for macOS. The goal is to provide a polished card-like widget experience close to native desktop widgets, while still allowing manual target-date setup, opacity control, and bilingual UI.

The project is currently optimized for personal use, but the codebase has already been reorganized to support ongoing iteration and public Git publishing.

## 2. Current Features

### 2.1 Core Features

- Supports a custom target date
- The target is date-based and shown in days, not hour-level target input
- Displays four progress sections:
  - Target remaining
  - Today remaining
  - Month remaining
  - Year remaining
- Each section includes a progress bar
- Supports Chinese and English
- Supports opacity adjustment
- Supports persistent local configuration
- Focus sessions: set duration in minutes or hours in the settings dialog; saving starts immediately; on successful completion a short fireworks animation plays, then the widget returns to the normal countdown view
- Completed focus time is aggregated per calendar day (total seconds and session count)
- Right-click menu opens a standalone Statistics window for the last 30 days (per-day duration and counts plus totals)

### 2.2 Interaction

- Frameless floating window
- Always-on-top behavior
- Draggable by left mouse button
- Double-click to open settings
- Right-click menu for:
  - Settings
  - Focus statistics window
  - Language switching
  - Quit

### 2.3 Visual State

- Finalized card size is `173 x 173` (about 10% smaller than the earlier 192 design)
- Rounded card with soft shadow and warm muted palette
- Single cat decoration at the top-right
- Chinese layout is the current visual baseline
- English layout uses its own offset parameters so it can be tuned independently

## 3. Confirmed Design Constraints

- The current Chinese layout should be treated as the baseline and should not be casually broken
- English layout may be tuned independently
- Target setup remains date-only
- Font size should not be reduced casually
- Text and bars should remain as a centered content block with internal left alignment
- Decorative assets should stay clean and free of obvious white/black edge artifacts

## 4. Stable Technical Decisions

- The project has been refactored from a single file into multiple modules
- Local runtime state uses `time_master_config.py`
- The repository keeps `time_master_config.example.py` as the committed example
- Publishing now follows standard Python dependency management instead of relying on committing `.pyside6_vendor/`

## 5. Likely Future Iteration Areas

- Further tune Chinese and English layouts
- Add more color themes
- Add more size variants
- Improve DMG distribution (signing, notarization, release polish)
- Move runtime config into a more standard app-specific local directory
- Improve screenshots, demo materials, and public-repo polish

## 6. Change Management Rules

- Decide first whether a change targets Chinese only, English only, or both
- For visual tweaks, update layout constants before touching business logic
- Do not commit personal runtime state files to Git (including `time_master_focus_stats.json` and similar)
- When adding major features, update this requirements document first
