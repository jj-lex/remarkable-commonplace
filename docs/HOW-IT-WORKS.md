# How it works

Commonplace is a single [qmldiff](https://github.com/asivery/qmldiff) patch file, `mod/commonplace.qmd`. When xovi starts, qt-resource-rebuilder applies it to the tablet's interface files in memory. Nothing on the tablet's system partition is changed.

## What the patch touches

| Interface file | Change |
|---|---|
| `/qml/common/Values.qml` | Shared state: whether ❝ is on, the notebook ID, the tool to restore afterwards |
| `/qt/qml/xofm/libs/toolbar/qml/Toolbar.qml` | The ❝ button, placed after the built-in editing tools. Tapping it switches to the capture tool. |
| `/qml/device/view/documentview/DocumentView.qml` | Everything else: reacting to a capture, the Save bar, making the card, the label, Back, Index and the open-in-book link |

## Capture flow

```
tap ❝ ──► selection tool in capture mode
draw loop ──► tablet cuts a clip ("snippet copied")
          ──► mod records book ID, title, author, page, capture area, time
Save / Save + note
  1. open the Commonplace notebook
  2. add a page at the end; wait until it is showing and settled
  3. paste the clip, centred horizontally
  4. type "Title — Author · p. N · date, time" at the top of the page
  5. tag the page with the book's title
  6. write the card's log file and update the index
  7. Save: return to the book page and restore your tool
     Save + note: stay, switch to the pen, show ← Back
```

The mod waits for each step to finish (polling every 250 ms) instead of using fixed delays, and gives up with a message after 25 seconds.

## Files on the tablet

All under `/home/root/commonplace/`:

### `config.json`

```json
{ "notebookId": "<ID of your Commonplace notebook>" }
```

Written by `scripts/install.sh`.

### `<card page ID>.json` — one per card

```json
{
  "id": "<book document ID>",
  "name": "<book name as shown on the tablet>",
  "fileType": 3,
  "page": 41,
  "pageId": "<book page ID>",
  "rect": { "x": -600.0, "y": 900.0, "w": 1100.0, "h": 520.0 },
  "pageCount": 320,
  "author": "<author as found>",
  "time": 1700000000000,
  "notebookId": "<Commonplace notebook ID>",
  "cardPage": 2,
  "cardPageId": "<card page ID>",
  "savedAt": 1700000004000
}
```

`page` is zero-based (the label shows `page + 1`). `rect` is the capture area in the book page's coordinates, so a sync tool can read the exact text inside it from the book file.

### `index.json`

A list of `{ cardPageId, sourceId, title, author, page, time }`, one per card, used by the Index panel.

## Finding the author

In order: the document's own author field, the library entry's author, then download-style file names (`Title -- Author -- …`). The label shows the surname only.
