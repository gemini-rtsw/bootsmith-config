# Shared target profiles

Each `*.json` file in this directory is one Bootsmith target. Commit them so
the team has a shared library of known boards.

Bootsmith reads/writes this directory by default when it's launched from the
repo root (or when `--profiles-dir ./profiles` is passed explicitly).

## On the boot server

`/var/lib/bootsmith/profiles` is a clone of this repo, created when the
bootsmith RPM is first installed. To change a preset:

1. Edit it in the Bootsmith web UI (or as a file), or open a PR here.
2. On the boot server, publish or take the change:

   ```sh
   cd /var/lib/bootsmith/profiles
   git pull                                      # take what was merged to main
   git add -A && git commit -m "..." && git push   # keep edits made in the UI
   ```

The app reads this directory on every page load, so no restart is needed.

## Migrating existing profiles

If you previously had profiles under `~/.bootsmith/profiles/`, copy them in:

```sh
cp ~/.bootsmith/profiles/*.json profiles/
git add profiles/*.json
git commit -m "REL-4933: Import target profiles"
```

## File format

```json
{
  "name": "MCS",
  "wti_host": "10.1.5.85",
  "wti_port": 2308,
  "loader_hint": "vxworks",
  "boot_params": {
    "boot_device": "geisc",
    "unit_number": "0",
    "host_name": "host",
    "file_name": "/tornado/mv2604/vxWorks",
    "...": "..."
  },
  "prompts": {},
  "banners": {},
  "notes": ""
}
```

The filename must match `name + ".json"` and `name` must be
`[A-Za-z0-9._-]{1,64}`.
