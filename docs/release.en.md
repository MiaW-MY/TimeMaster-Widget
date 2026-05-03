# macOS distribution (Tier B)

This project ships a **PyInstaller `.app`** and an optional **DMG** for a standard “download → open → drag to Applications” flow.

## What you build

| Artifact | Command | Notes |
|----------|---------|--------|
| `dist/Time Master.app` | `./scripts/build_mac_app.sh` | Double-clickable; bundles Python + PySide6. |
| `dist/Time-Master-<version>.dmg` | `./scripts/build_dmg.sh` | Same `.app` inside a disk image, plus an **Applications** shortcut. |

`build_dmg.sh` runs `build_mac_app.sh` automatically if the `.app` is missing.

Set **`VERSION`** to override the filename suffix (default: `git describe --tags --always`, or `0.0.0` if not in a git repo):

```bash
VERSION=1.0.0 ./scripts/build_dmg.sh
```

## GitHub Releases checklist

1. Tag a version (example): `git tag v1.0.0 && git push origin v1.0.0`
2. On GitHub: **Releases → Draft a new release**, choose the tag.
3. Attach **`Time-Master-*.dmg`** (and optionally a **zip of the `.app`** if you want a smaller alternative).
4. In the release description, list:
   - **macOS** minimum version you tested
   - **Apple Silicon vs Intel** (current PyInstaller build is whatever machine you built on; document it)
   - **First launch**: unsigned builds may require **System Settings → Privacy & Security → Open Anyway** (or right-click → Open once)

## End-user steps (what to paste in release notes)

1. Download the **`.dmg`** file.
2. Double-click it. A window opens with **Time Master.app** and **Applications**.
3. Drag **Time Master** into **Applications**.
4. Eject the DMG. From **Applications** (or Launchpad), open **Time Master**.

If macOS says the app cannot be opened because it is from an unidentified developer, open **System Settings → Privacy & Security** and approve it, or right-click the app → **Open** once.

## Data location

When run from the standalone app, config and focus stats live under:

`~/Library/Application Support/TimeMaster-Widget/`

## Later upgrades (signing / notarization)

Tier B is **unsigned** by default. To reduce Gatekeeper friction, use an Apple Developer ID to **sign** and **notarize** the `.app` or DMG; that is a separate step from this script.
