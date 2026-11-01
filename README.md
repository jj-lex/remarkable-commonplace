# Commonplace for reMarkable

A commonplace book for your reMarkable, made of notecards.

Readers have kept commonplace books for centuries: passages copied from what they read, with their own notes, gathered under topics and found again through an index. Commonplace does this on the tablet. Capture a passage while you read, drop it onto a notecard, and write your thoughts next to it — without leaving the book for more than a few seconds.

Commonplace is a small [xovi](https://github.com/asivery/xovi) mod for the reMarkable 2. It adds a **❝** button to the toolbar:

1. Tap **❝** and draw around the passage you want.
2. Choose **Save** (stay in the book) or **Save + note** (open the card to write on it).
3. The passage is pasted onto a new page at the end of your **Commonplace** notebook, labelled with the book's title, author, page and the date and time you captured it.
4. **Save** takes you straight back to your page. **Save + note** switches to the pen so you can write, with a **← Back to p. N** button to return.

Inside the Commonplace notebook you also get:

- **Index** — every card you've made, newest first, with one tap to the card or back to the passage in the book.
- **Open p. N ↗** — on any card, jumps back to the page it came from.

Every card is also logged as a small JSON file on the tablet (book, page, capture area, time), so a sync tool on your computer can build a searchable catalog of quotes. That sync is the next part of this project.

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

See the **[setup guide](docs/SETUP.md)**. In short: enable SSH, install xovi and its resource rebuilder, create a notebook called *Commonplace*, then run:

```bash
./scripts/install.sh root@10.11.99.1
```

## How it works

See [docs/HOW-IT-WORKS.md](docs/HOW-IT-WORKS.md) for the capture flow and the files the mod writes.

## Roadmap

- [ ] Mac sync: turn each card into a note in an Obsidian vault (quote text, book, author, page, your handwriting)
- [ ] Rectangle capture (drag corner to corner instead of drawing a loop)
- [ ] Highlight the captured passage in the book automatically

## Credits

- [xovi](https://github.com/asivery/xovi) and [qt-resource-rebuilder / qmldiff](https://github.com/asivery/rm-xovi-extensions) by asivery — the framework that makes interface mods possible
- [ingatellent/xovi-qmd-extensions](https://github.com/ingatellent/xovi-qmd-extensions) — reference mods for firmware 3.29

Not affiliated with or endorsed by reMarkable AS. This repository contains only original patch files; no reMarkable software is included.

## License

[MIT](LICENSE)
