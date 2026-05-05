# Build and publish (macOS)

This document is for **maintainers**: produce the **PyInstaller `.app`**, optional **DMG**, and ship on **GitHub Releases**. End users who only download a build can skip this and follow the install steps in the repo [README](../README.md).

## Prerequisites

- **macOS**, **Python 3.10+**.
- Clone the repo and use a **project-local** virtualenv (same as “run from source” in the README):

```bash
cd /path/to/TimeMaster-Widget
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

**Tip:** If you accidentally created `.venv` in your **home** directory, remove `~/.venv`, `cd` into the real project folder, then create `.venv` again there.

## Build the standalone `.app`

From the **repository root**, with `.venv` activated and dependencies installed:

```bash
./scripts/build_mac_app.sh
```

Writes **`dist/Time Master.app`** (PyInstaller; dev extras in `requirements-dev.txt`).

**App icon:** The bundle uses **`assets/AppIcon.icns`**, generated from **`assets/app_icon_1024.png`**. Prefer a roughly **1024×1024** square with no huge empty margin. To refresh the icon: `python3 scripts/make_app_icon.py` (after `pip install -r requirements-dev.txt`), then run **`build_mac_app.sh`** again.

**Gatekeeper:** Unsigned builds may need **System Settings → Privacy & Security** or **right-click the app → Open** until you code-sign for distribution.

## Build the DMG

After **`dist/Time Master.app`** exists:

```bash
./scripts/build_dmg.sh
```

If the `.app` is missing, **`build_dmg.sh`** runs **`build_mac_app.sh`** first.

Produces an **uncompressed** read-only **DMG** (`UDRO`) containing **Time Master.app** and an **Applications** alias — typical “drag to Applications” UX.

**Output:** `dist/Time-Master-<version>.dmg` — version from `git describe --tags --always`, or override:

```bash
VERSION=1.0.0 ./scripts/build_dmg.sh
```

## Ship on GitHub Releases

1. **Commit and push** everything you want on the default branch.
2. **Tag** and push, e.g. `git tag v1.0.0 && git push origin v1.0.0` (use your version).
3. On GitHub: **Releases → Draft a new release** → choose that tag → attach **`dist/Time-Master-*.dmg`** (optional: zip of the `.app`).
4. In the **release description**, document:
   - **Minimum macOS** you tested  
   - **Apple Silicon vs Intel** for the machine you built on (PyInstaller output matches the host)  
   - Short **first-launch / Gatekeeper** guidance (same ideas as above)

**Day-to-day:** work from a clone with `python3 time_master.py`; when you cut a release, rebuild and attach the new DMG. Config while developing lives next to the repo; the installed app uses **Application Support** — copy files manually if you migrate between the two.

## End-user steps (paste into release notes)

1. Download the **`.dmg`** file.
2. Double-click it. A window opens with **Time Master.app** and **Applications**.
3. Drag **Time Master** into **Applications**.
4. Eject the DMG. From **Applications** (or Launchpad), open **Time Master**.

If macOS says the app cannot be opened because it is from an unidentified developer, open **System Settings → Privacy & Security** and approve it, or right-click the app → **Open** once.

## Data location (standalone app)

When run from the packaged app, settings and focus stats live under:

`~/Library/Application Support/TimeMaster-Widget/`

## Later: signing and notarization

Default builds are **unsigned**. To reduce Gatekeeper friction, use an Apple **Developer ID** to **sign** and **notarize** the `.app` or DMG; that is separate from these scripts.
