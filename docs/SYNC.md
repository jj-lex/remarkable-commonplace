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
- **Handwriting** is read by Apple's on-device Vision text recognition by default. Approximate for messy writing; the image is always there too. A vision LLM (Claude, GPT, Grok…) does much better — see *Bring your own model*.
- **Topics** come from Apple's on-device language model by default (macOS 26+, Apple silicon, Apple Intelligence on). 1–3 per notecard, reusing existing topics where they fit. Small model, so expect the odd miss — swap in a bigger model, or edit the note's `topics` property and it sticks.

- **One notebook per year**: the sync looks for notebooks named *Commonplace YYYY* in the *Commonplace* folder and points the mod at this year's. If it doesn't exist yet, notecards keep going into the newest one and you get one reminder to create it.
- **Health**: if the tablet fully restarted, the sync switches the mod back on. You get one notification if Wi-Fi SSH starts accepting passwords again (firmware updates do this) or if the tablet hasn't been reachable for 3 days.

Only these two steps use AI. Everything else — pulling from the tablet, passage text, book details, notes and pages — is ordinary code.

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

## Bring your own model

Topics and handwriting each use a *provider*, set separately in your settings file. The default is `apple` (on device, free, private). Swap either one for a hosted or local model:

| `provider` | What it is | Needs |
|---|---|---|
| `apple` | Apple's on-device model + Vision (default) | macOS 26, Apple silicon, Apple Intelligence on |
| `anthropic` | Claude, via the official Anthropic SDK | API key; default model `claude-opus-5-5`, low effort |
| `openai` | OpenAI | API key, `"model"` |
| `xai` | xAI (Grok) | API key, `"model"` |
| `openrouter` | OpenRouter (hundreds of models) | API key, `"model"` |
| `ollama` | Local models via Ollama | Ollama running, `"model"` |
| `openai-compatible` | Anything that speaks the OpenAI chat format (Groq, Together, LM Studio, vLLM…) | `"base_url"`, `"model"`, usually a key |
| `none` | Skip this step | — |

Examples — Claude reads handwriting, Apple keeps doing topics:

```json
"ai": {
  "topics":      { "provider": "apple" },
  "handwriting": { "provider": "anthropic" }
}
```

Grok for both:

```json
"ai": {
  "topics":      { "provider": "xai", "model": "<model name from xAI's docs>" },
  "handwriting": { "provider": "xai", "model": "<a vision-capable model>" }
}
```

A local model through Ollama (no key, nothing leaves your Mac):

```json
"ai": { "topics": { "provider": "ollama", "model": "<a model you've pulled>" } }
```

Model names change often, so apart from Claude none is assumed — use the name from your provider's docs. For handwriting, pick a model that accepts images.

**API keys** are never stored in the settings file. The sync looks for an environment variable (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `XAI_API_KEY`, `OPENROUTER_API_KEY`), then macOS Keychain. The background job doesn't see your shell's environment, so Keychain is the reliable place:

```bash
security add-generic-password -a "$USER" -s commonplace-anthropic -w   # prompts for the key
security add-generic-password -a "$USER" -s commonplace-openai -w
security add-generic-password -a "$USER" -s commonplace-xai -w
```

Use a different Keychain entry or variable with `"api_key_keychain"` / `"api_key_env"`.

**Privacy:** with a hosted provider, the passage text (topics) or your handwriting image (handwriting) is sent to that provider. The default `apple` provider sends nothing anywhere.

If a provider is misconfigured or unreachable, the sync logs why and skips that step for the run — notes still sync.

**Adding a provider:** implement `complete(system, prompt, max_tokens)` and `read_image(png, prompt)` in `sync/commonplace_sync/providers.py` and register it in `make()`. Prompts and clean-up live in `ai.py` and are shared by every provider.

## Settings

`~/Library/Application Support/Commonplace/config.json`:

```json
{
  "vault_dir": "~/path/to/vault/Books & Reading/Commonplace",
  "hosts": ["remarkable-wifi", "remarkable"],
  "wifi_host": "remarkable-wifi",
  "timezone": "America/New_York",
  "recent_days": 14,
  "unreachable_alert_days": 3,
  "ai": {
    "topics":      { "provider": "apple" },
    "handwriting": { "provider": "apple" }
  }
}
```

Set `wifi_host` to `""` to skip the Wi-Fi password check.

`timezone` is any IANA name (`Europe/London`, `Asia/Tokyo`…); leave it empty to use your Mac's. The tablet's clock runs on UTC, so each sync tells the mod the current offset for your zone — notecard labels show your local time, including after daylight-saving changes.
