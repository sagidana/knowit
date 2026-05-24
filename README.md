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
knowit push                   # upload notes to a 1Password vault
knowit pull                   # download notes from a 1Password vault
```

`--cwd <path>` sets the notes directory (default: `~/notes`).

## Syncing with 1Password

`knowit` can sync notes to a 1Password vault using the official 1Password SDK
and a [Service Account](https://developer.1password.com/docs/service-accounts/)
token. `push` and `pull` work like their `git` counterparts: each operates in a
single direction and overwrites the destination, with no automatic merge.

Provide the service account token by writing it to `~/.config/knowit/.token`:

```bash
mkdir -p ~/.config/knowit
printf 'ops_...' > ~/.config/knowit/.token   # service account with vault access
chmod 600 ~/.config/knowit/.token

knowit push                   # local notes -> vault (create/update items)
knowit pull                   # vault -> local notes (create/update files)
knowit push --vault MyNotes   # target a vault other than the default "Notes"
```

The `OP_SERVICE_ACCOUNT_TOKEN` environment variable, if set, takes precedence
over the token file — useful for runtime injection (e.g. `op run`).

Each note is stored as a Secure Note item titled with the note's path relative
to the notes directory (the key used to match files to items), with the note's
`#tags` mirrored onto the item. Both directions are additive — deletions are not
propagated.

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
