# Section Synced Document Viewer Design

## Goal

Fix the current document viewer data semantics so section selection drives both original text and parsed analysis panes consistently.

The current bug is that uploaded `DocumentUnit` records are converted into parsed content blocks with a synthetic `uploaded-content` section id. This makes real PageIndex sections ineffective, and it also makes the parsed pane show original text even when no AI analysis has been generated.

## Scope

Included:

- Frontend section selection loads original units through `GET /api/sections/{section_id}/content`.
- Original text pane displays the selected section's `DocumentUnit` records and scrolls to the section start by replacing the displayed unit list.
- Parsed pane only displays real parsed or analysis content blocks when they exist for the selected section.
- If no parsed content exists for the selected section, the parsed pane shows an empty parsed-state message instead of original text.
- Upload flow builds and loads the section tree, then selects the first section when available.
- Regression tests cover section-driven original text and parsed empty state.

Excluded:

- Generating AI analysis content.
- New analysis persistence schema or API.
- Complex nested PageIndex reconstruction beyond the existing section tree API.

## UX Rules

- `原文` means extracted source text from `DocumentUnit`.
- `解析` means AI-produced parsed or analysis content only.
- Without AI analysis, `解析` must be empty even if source text exists.
- Selecting a section updates both panes:
  - `原文` shows the selected section's source units.
  - `解析` filters by the same section id and shows empty state if no matching content exists.
- If a document has no section tree, the viewer may show the full source units in the original pane and keep parsed content empty.

## Architecture

### API Layer

Add a frontend wrapper for the existing backend endpoint:

- `getSectionContent(sectionId)` -> `GET /api/sections/{sectionId}/content`

The response maps to the same minimal shape as `DocumentUnit`.

### Workspace State

Keep separate data for:

- Full document units by file id.
- Currently visible source units by selected section.
- Parsed content blocks by file id.
- Sections by file id.

Do not use `unitsToContentBlocks(detail.units)` as a parsed-content fallback.

### Viewer Rendering

`DocumentViewer` receives:

- `units`: source units for the active selection.
- `contentBlocks`: parsed content blocks only.
- `selectedSectionId`: selected section.
- `viewerStatus`: high-level loading or ready state.

The parsed pane computes filtered content from `contentBlocks` and `selectedSectionId`. If ready but no parsed blocks match, it shows a parsed empty message.

## Error Handling

- If section content loading fails, keep the section selected, clear visible source units for that selection, and show an error state or upload error text.
- Section tree build failure should not block full source display, but parsed remains empty.
- Upload failure continues to clear stale content.

## Tests

- Component/page test: after upload with sections, selecting a section calls section content API and original pane shows that section's source text only.
- Component/page test: after upload with source units but no parsed content, parsed pane shows empty parsed message and does not show source text in parsed content.
- API wrapper test: `getSectionContent` calls `/sections/{sectionId}/content` and returns units.
- Existing `DocumentViewer` tests updated so source text and parsed text are not conflated.

## Acceptance Criteria

- Clicking a PageIndex section changes the original pane to that section's source text.
- Clicking a PageIndex section changes the parsed pane to that section's parsed result if present.
- If no parsed result exists, parsed pane is empty and does not show original text.
- Uploading a parsed document no longer creates fake parsed blocks from `DocumentUnit`.
- Existing upload, empty, and error states remain covered by tests.
