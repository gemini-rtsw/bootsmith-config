# bootsmith-config

The boot-parameter presets for [bootsmith](https://github.com/gemini-rtsw/bootsmith),
one JSON file per preset. This repo is the source of truth: the copy on the
bootsmith host (`/var/lib/bootsmith/profiles` on `mkoswgdkr-lv1`) is a git
clone of it.

**This repo is public.** Never put passwords or tokens in a preset.

## How the pieces fit

- bootsmith reads `/var/lib/bootsmith/profiles` on every page load. A new or
  changed file there shows up on the next refresh, with no restart.
- Saving in the bootsmith UI writes the file there immediately. It does
  **not** touch any crate and does **not** commit to git.
- `main` is protected: changes reach it through a pull request.
- So every change ends with two steps: get it into `main` (PR), and get `main`
  onto the host. Do both the same day so the host and git never drift.

## Add or change a preset

Two ways. Use the UI for edits made on the host; use a branch and PR when
you prepare a change ahead of time (for example for a TR).

### A. In the bootsmith UI, then commit from the host

1. Open http://mkoswgdkr-lv1:8080/ and go to the system (e.g. `SCS`).
   - **Duplicate** an existing preset to start from known-good values (the
     usual way to make a `-new-bootserver` variant), then **Edit** it.
   - **+ New preset** adds a blank preset to that system.
   - **+ New system** creates a system with its first console and preset.
2. Save. The JSON file is now in `/var/lib/bootsmith/profiles`.
3. Commit and push it from the host (next section).

### B. On a branch, then a PR

```sh
git clone git@github.com:gemini-rtsw/bootsmith-config.git
cd bootsmith-config
git switch -c REL-1234
cp MKO-PROD-SCS.json MKO-PROD-SCS-new-bootserver.json
# edit the new file: set "name" to match the filename, change what differs
git add MKO-PROD-SCS-new-bootserver.json
git commit -m "SCS: add new-bootserver preset (REL-1234)"
git push -u origin REL-1234          # open the PR from the link git prints
```

After it is merged, load it on the host (see "Take changes merged on GitHub").

## Commit and push changes made on the host

Log in with agent forwarding so your own GitHub key does the push:

```sh
ssh -A mkoswgdkr-lv1.hi.gemini.edu
cd /var/lib/bootsmith/profiles
git status                     # what changed
git diff                       # check it
git switch -c REL-1234         # main is protected: work on a branch
git add -A
git commit -m "GNIRSCC: point new-bootserver preset at 10.2.2.145 (REL-1234)"
git push -u origin REL-1234    # open the PR from the link git prints
```

After the PR is merged, put the host back on `main`:

```sh
git switch main
git fetch origin && git merge --ff-only origin/main
git branch -d REL-1234
```

Commit messages: start with the system, say what changed and why, and give
the ticket.

## Take changes merged on GitHub

```sh
cd /var/lib/bootsmith/profiles
git fetch origin && git merge --ff-only origin/main
git log --oneline -1           # should match main on GitHub
ls | grep <SYSTEM>             # the new preset is there
```

No restart: reload the bootsmith page.

`git pull` does the same in one step, but it can hang when github.com is slow
or unreachable from the host (seen 2026-11-18). If it does, Ctrl-C and run
`git fetch` and `git merge --ff-only` separately: the merge needs no network
once the fetch has finished.

## Test a preset branch for a TR

```sh
cd /var/lib/bootsmith/profiles
git fetch origin REL-1234:REL-1234 && git checkout REL-1234
# ... TR ...
git checkout main
```

## When git can't reach GitHub

You can copy a preset in by hand to try it:

```sh
scp MKO-PROD-SCS-new-bootserver.json mkoswgdkr-lv1:/var/lib/bootsmith/profiles/
```

Delete the copied file before the next `git merge`/`git pull`, or git refuses
to overwrite it. This is temporary: the preset still has to go in by PR.

## File format

The filename must be `<name>.json`, and `name` must match
`[A-Za-z0-9._-]{1,64}`. Name presets `<SITE>-<ENV>-<SYSTEM>[-variant]`, for
example `MKO-PROD-GNIRSCC-new-bootserver`.

```json
{
  "name": "MKO-PROD-SCS-new-bootserver",
  "system": "SCS",
  "loader_hint": "ppcbug",
  "reboot": "",
  "terminal_servers": [
    {"name": "production", "host": "10.2.2.19", "port": 5007}
  ],
  "boot_params": {
    "client_ip": "10.2.2.107",
    "server_ip": "10.2.2.145",
    "boot_file_name": "/gem_base/epics/ioc/scs_mk/scs.boot",
    "argument_file_name": "/gem_base/epics/ioc/scs_mk/stscs",
    "...": "..."
  },
  "prompts": {},
  "banners": {},
  "notes": "Rollback: MKO-PROD-SCS."
}
```

| Field | Meaning |
|---|---|
| `name` | Preset name; must equal the filename without `.json`. |
| `system` | The board this preset is for (`SCS`, `GMOSCC`, `GNIRSDC1`), upper case. Presets are grouped by it, and a preset can only be used on that system's consoles. |
| `loader_hint` | `ppcbug` (RTEMS/PPCBug boards), `vxworks`, or `auto`. Advisory: bootsmith detects the loader at the prompt anyway. |
| `reboot` | How to reboot the crate from its running OS, as typed on the console. `^X` is Ctrl-X; text is sent followed by Enter (`exit` on RTEMS/EPICS 7, `dbpf <prefix>:iocStats:SysReset 1` on 3.14 with iocStats). Blank = Ctrl-X on vxWorks; RTEMS has no default, so the Reboot button stays off until it is set. |
| `terminal_servers` | The consoles (WTI host:port) this preset may be used on. Presets that list the same host:port share one connection. |
| `boot_params` | The values written to the boot ROM. Keys depend on the loader (PPCBug `niot`/`env` fields, or the vxWorks boot line). |
| `prompts`, `banners` | Optional overrides of the prompt/banner match strings for unusual ROM versions. Usually `{}`. |
| `notes` | Free text shown in the UI: what the preset is for, its rollback preset. |

Boot-parameter values: blank keeps the board's current value, a single `.`
clears the field, anything else is written as-is. On PPCBug, `.` or `NULL`
means "no value" for the boot and argument file names.

PPCBug's boot file and argument file fields are short, so long install paths
don't fit. Point them at short symlinks shipped by the IOC's RPM (for example
scs_mk's `scs.boot` and `stscs`) rather than the full `bin/<arch>/...` path.

## Testing a new preset

1. **Connect** to the console in bootsmith. This does nothing to the crate.
2. Get the crate to its boot prompt (**Reboot**, or from the console).
3. **Push to board** writes and reads back every parameter. Fix anything it
   lists as not read back.
4. **Boot**, and watch the console for the server IP and the files it loads.
5. Keep the old preset: rolling back is pushing it and booting again.
