# knowit

A tag-based note browser for the terminal. Notes are plain markdown files; `knowit` lets you navigate them interactively using tags, fuzzy search, and grep.

## Install

```bash
pip install .
```

`fzf` and `bat` are downloaded automatically into `~/.knowit/bin/` on first use — no system-level dependencies required.

To force a reinstall of the bundled tools:

```bash
knowit install
```

## Usage

```bash
knowit -a browse              # browse notes by tag
knowit -a create              # create a new note
knowit -a view   -t <tag>...  # open all notes matching tags
knowit -a grep   -t <tag>...  # full-text search within matching notes
knowit -a link   -t <tag>...  # pick a note path (for use in links)
knowit -a tag    -t <tag>...  # select tags interactively
```

`--cwd <path>` sets the notes directory (default: `~/notes`).

## Key bindings (inside fzf)

| Key | Action |
|-----|--------|
| `tab` | Toggle tag filter |
| `enter` | Open selected note |
| `ctrl-t` | Create new note |
| `ctrl-g` | Switch to grep search |
| `ctrl-z` | Toggle preview |
| `ctrl-j/k` | Scroll preview down/up |
| `ctrl-d/u` | Scroll preview half page |
| `esc` | Remove last tag filter |

## Note format

Each note is a plain markdown file with a header line:

```
[2024-03-01 12:00:00] #tag1 #tag2

---
Your content here.
```

## Bundled tool versions

| Tool | Version |
|------|---------|
| fzf  | 0.62.0  |
| bat  | 0.25.0  |
