# Mac sync

Turns every notecard into a note in an Obsidian vault, every 15 minutes while your Mac is awake. Everything runs on your Mac; nothing is sent anywhere.

## What you get

In the folder you choose (for example `Books & Reading/Commonplace`):

| Path | What it is |
|---|---|
| `Notecards/` | One note per notecard: the passage text, title, author, page, capture time, the clip, your handwriting (image and text), topics, and a link that opens the saved book at that page |
| `Books/` | One page per book, its notecards in page order |
| `Topics/` | One page per topic, notecards from every book |
| `Recent.md` | The last two weeks, newest first |
| `Commonplace.md` | Everything, by book, plus all topics |
| `_sources/` | A copy of each book you've quoted from (only those), so passages outlive the book on the tablet |
| `_assets/` | Clips and handwriting images |

Write anything you like below the line `%% Everything above this line is updated by Commonplace sync. %%` in a notecard — the sync never touches it. Topics you change in a note's properties are kept.

## How the pieces work

- **Passage text** is read from the book file inside the area you captured (the mod logs it). No OCR needed for EPUBs and text PDFs. Scanned PDFs show "picture only".
- **Handwriting** is recognized with Apple's on-device Vision text recognition. Approximate for messy writing; the image is always there too.
- **Topics** come from Apple's on-device language model (macOS 26+, Apple silicon, Apple Intelligence on). 1–3 per notecard, reusing existing topics where they fit. Small model, so expect the odd miss — edit the note's `topics` property and it sticks.
- **Health**: if the tablet fully restarted, the sync switches the mod back on. You get one notification if Wi-Fi SSH starts accepting passwords again (firmware updates do this) or if the tablet hasn't been reachable for 3 days.

## Install

Requirements: macOS 26 on Apple silicon (for topics; everything else works on older macOS), Xcode command-line tools (`xcode-select --install`), and SSH access to the tablet set up as in [SETUP.md](SETUP.md) — with `remarkable-wifi` and/or `remarkable` hosts in `~/.ssh/config`.

```bash
./scripts/install-sync.sh "$HOME/path/to/vault/Books & Reading/Commonplace"
```

This creates a Python environment, builds the small Swift helper, writes your settings to `~/Library/Application Support/Commonplace/config.json`, and registers a background job that runs now and every 15 minutes.

The first run may show a macOS prompt asking to allow access to devices on your local network — allow it, or the sync can't reach the tablet.

## Everyday

Nothing to do. Read, capture, write — notes appear in your vault within 15 minutes of the tablet being awake on Wi-Fi.

- Log: `~/Library/Logs/Commonplace/sync.log`
- Run now: `launchctl kickstart -k gui/$(id -u)/com.github.commonplace.sync`
- Stop: `./scripts/uninstall-sync.sh`

## Settings

`~/Library/Application Support/Commonplace/config.json`:

```json
{
  "vault_dir": "~/path/to/vault/Books & Reading/Commonplace",
  "hosts": ["remarkable-wifi", "remarkable"],
  "wifi_host": "remarkable-wifi",
  "recent_days": 14,
  "unreachable_alert_days": 3
}
```

Set `wifi_host` to `""` to skip the Wi-Fi password check.
