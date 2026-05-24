"""
Sync knowit notes with a 1Password vault using the official 1Password SDK.

Auth is via a 1Password Service Account token read from
~/.config/knowit/.token (or the OP_SERVICE_ACCOUNT_TOKEN environment variable,
which takes precedence). Each note is stored as a Secure
Note item whose title is the note's path relative to the notes directory; that
relative path is the stable key used to match local files <-> vault items, so
repeated push/pull operations update items in place instead of duplicating them.

The full note file is stored verbatim in the item's notes body (lossless
round-trip), and the note's #tags are mirrored to the item's tags so they remain
filterable in the 1Password UI.

`push` uploads local -> vault, `pull` downloads vault -> local. Each direction
is additive and overwrites the destination (like `git push` / `git pull`); no
automatic merge or conflict resolution is performed, and deletions are not
propagated.
"""
import os
from os import path, walk

from knowit.note import Note

INTEGRATION_NAME = "knowit"
INTEGRATION_VERSION = "0.1.0"

# Default on-disk location for the service account token.
TOKEN_FILE = path.expanduser("~/.config/knowit/.token")


def _read_token():
    """Return the 1Password service account token.

    The OP_SERVICE_ACCOUNT_TOKEN environment variable takes precedence (handy
    for runtime injection, e.g. `op run`); otherwise the token is read from
    TOKEN_FILE.
    """
    token = os.environ.get("OP_SERVICE_ACCOUNT_TOKEN", "").strip()
    if token:
        return token

    try:
        with open(TOKEN_FILE) as f:
            token = f.read().strip()
    except FileNotFoundError:
        token = ""
    if token:
        return token

    raise RuntimeError(
        f"No 1Password service account token found. Write the token to "
        f"{TOKEN_FILE} (and `chmod 600` it), or set OP_SERVICE_ACCOUNT_TOKEN."
    )


async def _client():
    token = _read_token()
    from onepassword.client import Client
    return await Client.authenticate(
        auth=token,
        integration_name=INTEGRATION_NAME,
        integration_version=INTEGRATION_VERSION,
    )


async def _resolve_vault_id(client, vault_name):
    vaults = await client.vaults.list()
    titles = []
    for vault in vaults:
        if vault.title == vault_name:
            return vault.id
        titles.append(vault.title)
    available = ", ".join(titles) or "(none)"
    raise RuntimeError(
        f"Vault '{vault_name}' not found. Available vaults: {available}"
    )


def _iter_local_notes(cwd):
    """Yield (title, raw_text, tags) for every valid note under cwd.

    title is the file's path relative to cwd, normalized to forward slashes so
    it is stable across platforms and usable as a 1Password item title.
    """
    for root, _dirs, files in walk(cwd):
        for f in files:
            file_path = path.join(root, f)
            try:
                note = Note.parse(file_path)
            except Exception:
                continue
            with open(file_path, "r") as fp:
                raw = fp.read()
            title = path.relpath(file_path, cwd).replace(os.sep, "/")
            yield title, raw, note.tags


def _make_item_params(vault_id, title, raw, tags):
    # The Secure Note body lives in the item's top-level `notes` attribute;
    # there is no dedicated NOTES field type in the SDK.
    from onepassword import ItemCategory, ItemCreateParams
    return ItemCreateParams(
        title=title,
        category=ItemCategory.SECURENOTE,
        vault_id=vault_id,
        notes=raw,
        tags=list(tags),
    )


async def push(cwd, vault_name):
    """Upload local notes to the vault, creating or updating items in place."""
    client = await _client()
    vault_id = await _resolve_vault_id(client, vault_name)

    remote = {}
    for overview in await client.items.list(vault_id):
        remote[overview.title] = overview.id

    created = updated = skipped = 0
    for title, raw, tags in _iter_local_notes(cwd):
        if title not in remote:
            await client.items.create(_make_item_params(vault_id, title, raw, tags))
            created += 1
            continue

        item = await client.items.get(vault_id, remote[title])
        if item.notes == raw and set(item.tags or []) == set(tags):
            skipped += 1
            continue
        item.notes = raw
        item.tags = list(tags)
        await client.items.put(item)
        updated += 1

    return {"created": created, "updated": updated, "skipped": skipped}


async def pull(cwd, vault_name):
    """Download vault items into the local notes directory."""
    from onepassword import ItemCategory
    client = await _client()
    vault_id = await _resolve_vault_id(client, vault_name)

    created = updated = skipped = 0
    for overview in await client.items.list(vault_id):
        if overview.category != ItemCategory.SECURENOTE:
            # Not a knowit note — leave it alone.
            skipped += 1
            continue
        item = await client.items.get(vault_id, overview.id)
        raw = item.notes
        if not raw:
            skipped += 1
            continue

        rel = overview.title.replace("/", os.sep)
        dest = path.join(cwd, rel)
        if path.exists(dest):
            with open(dest, "r") as fp:
                if fp.read() == raw:
                    skipped += 1
                    continue
            _write_file(dest, raw)
            updated += 1
        else:
            _write_file(dest, raw)
            created += 1

    return {"created": created, "updated": updated, "skipped": skipped}


def _write_file(dest, raw):
    parent = path.dirname(dest)
    if parent and not path.exists(parent):
        os.makedirs(parent, exist_ok=True)
    with open(dest, "w") as fp:
        fp.write(raw)
