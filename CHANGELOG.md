# Changelog

## 0.4.0 — 2026-11-01

- **Bring your own model** for topics and handwriting, set separately: `apple` (default, on device), `anthropic` (official SDK, Claude Opus 5.5 at low effort), `openai`, `xai`, `openrouter`, `ollama`, any `openai-compatible` endpoint, or `none`
- API keys from Keychain or environment variables, never the settings file
- Prompts and topic clean-up shared by every provider; a misconfigured provider skips its step instead of stopping the sync

## 0.3.0 — 2026-11-01

- **Mac sync** to Obsidian: one note per notecard (passage text from the book file, title, author, page, capture time, clip, handwriting image), Books / Topics / Recent / overview pages, a saved copy of each quoted book
- Handwriting recognized as text with Apple's on-device Vision
- Topics from Apple's on-device language model, reusing existing topics; your edits are kept
- The sync switches the mod back on after a tablet restart, and notifies you about Wi-Fi password login coming back or the tablet being unreachable
- `install-sync.sh` / `uninstall-sync.sh` and a background job every 15 minutes

## 0.2.0 — 2026-11-01

- Renamed to **Commonplace**: a commonplace book made of notecards (index title, Notecard / Source buttons, mod file, data folder, repo)
- A diagonal capture stroke now highlights the passage in the book, using the tablet's own snap-to-text highlighter
- Tried rectangle capture by cropping a screenshot: the reMarkable 2's display crashes on screenshots, so it's not included

## 0.1.0 — 2026-11-01

First working version on reMarkable 2, firmware 3.29.1.0.

- ❝ toolbar button that switches to the capture tool
- Save / Save + note bar after a capture
- Cards added to the end of the Commonplace notebook, clip centred, labelled with title, author, page, date and time, and tagged with the book's title
- Save returns to the book page and restores your previous tool; Save + note switches to the pen and shows ← Back
- Index panel and an "Open p. N" link on every card
- Per-card JSON log and an index file for a future computer sync
- Notebook ID read from a settings file instead of the code
- Install and uninstall scripts, setup guide
