# Commonplace for reMarkable

A commonplace book for your reMarkable, made of notecards.

Readers have kept commonplace books for centuries: passages copied from what they read, with their own notes, gathered under topics and found again through an index. Commonplace does this on the tablet. Capture a passage while you read, drop it onto a notecard, and write your thoughts next to it — without leaving the book for more than a few seconds.

Commonplace is a small [xovi](https://github.com/asivery/xovi) mod for the reMarkable 2. It adds a **❝** button to the toolbar:

1. Tap **❝**, then drag diagonally from the first word of the passage to the last (or draw a loop around it).
2. Choose **Save** (stay in the book) or **Save + note** (open the card to write on it).
3. The passage is pasted onto a new page at the end of this year's notebook (*Commonplace 2026*, in a *Commonplace* folder), labelled with the book's title, author, page and the date and time you captured it.
4. A diagonal stroke also **highlights the passage in the book**, so you see it when you reread.
5. **Save** takes you straight back to your page. **Save + note** switches to the pen so you can write, with a **← Back to p. N** button to return.

Inside the Commonplace notebook you also get:

- **Index** — every card you've made, newest first, with one tap to the card or back to the passage in the book.
- **Open p. N ↗** — on any card, jumps back to the page it came from.

On your Mac, the **sync** turns every notecard into a note in your Obsidian vault — passage text, title, author, page, capture time, your handwriting (as an image and as text), topics, and a link that opens the book at that page — plus a page per book and per topic. It runs every 15 minutes in the background. Handwriting and topics use Apple's on-device models by default, so nothing leaves your Mac — or plug in your own model (Claude, OpenAI, Grok, OpenRouter, Ollama, anything OpenAI-compatible) with one setting. See [docs/SYNC.md](docs/SYNC.md#bring-your-own-model).

## Status

Early, personal-use software. Tested on:

| Device | Firmware |
|---|---|
| reMarkable 2 | 3.29.1.0 |

Mods hook into the tablet's interface, which changes between firmware versions. **Don't update the tablet's firmware without checking that the mod still works** (see [Updating firmware](docs/SETUP.md#after-a-firmware-update)).

## Safety

- xovi is *tethered*: it does not start on boot. **Rebooting the tablet always returns it to stock.**
- The mod only adds pages to your Commonplace notebook and writes files to `/home/root/commonplace/`. It never changes your books.
- Take a backup before installing anything (the setup guide shows how).

## Install

See the **[setup guide](docs/SETUP.md)**. In short: enable SSH, install xovi and its resource rebuilder, create a *Commonplace* folder with a *Commonplace 2026* notebook inside, then run:

```bash
./scripts/install.sh root@10.11.99.1
```

Then, on your Mac:

```bash
./scripts/install-sync.sh "$HOME/path/to/vault/Books & Reading/Commonplace"
```

## How it works

See [docs/HOW-IT-WORKS.md](docs/HOW-IT-WORKS.md) for the capture flow and the files the mod writes, and [docs/SYNC.md](docs/SYNC.md) for the Mac sync.

## Roadmap

- [x] Mac sync to Obsidian: passage text, details, handwriting as text, topics, book and topic pages
- [x] Highlight the captured passage in the book (diagonal stroke)
- [x] Restart the mod automatically after the tablet reboots (done by the sync)
- [ ] Rectangle capture, highlighting from a loop, and a margin above and below the highlight — parked: these need a native helper that can create pen lines, which mods can't do on their own

## Known limits

- Highlighting only works with a diagonal stroke. Start just above the first line and end just below the last, or the first or last line can be missed.
- The clip follows the shape you draw. A loop gives a loop-shaped clip.
- After the tablet fully restarts (power off, flat battery, crash, firmware update) the mod is off until xovi is started again — the Mac sync does this for you within 15 minutes. Sleep is fine.
- Topics come from a small on-device model and are sometimes off. Edit them in a note's properties; your edits stick.

## Credits

- [xovi](https://github.com/asivery/xovi) and [qt-resource-rebuilder / qmldiff](https://github.com/asivery/rm-xovi-extensions) by asivery — the framework that makes interface mods possible
- [ingatellent/xovi-qmd-extensions](https://github.com/ingatellent/xovi-qmd-extensions) — reference mods for firmware 3.29

Not affiliated with or endorsed by reMarkable AS. This repository contains only original patch files; no reMarkable software is included.

## License

[MIT](LICENSE)
