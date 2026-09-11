# ARRIVE CLI — Linux (git-tracked dist)

Git-tracked Linux `arrive` CLI tarball so Cursor Cloud agents (and other
x86_64 Linux/glibc VMs) can install a pinned version without network access.

## Current artifact

| File | Description |
|------|-------------|
| `arrive-cli-v0.1.7-linux-x86_64.tar.gz` | `arrive` binary + templates + `install-from-tarball.sh` |
| `SHA256SUMS` | Checksum for the tarball in this directory |

## Install

From a clone of this repo, run the helper (verifies checksum, extracts, installs
to `~/.local/bin`, and seeds `~/.arrive/templates`):

```bash
./scripts/install-arrive-cli.sh
export PATH="$HOME/.local/bin:$PATH"
arrive --version
```

Target: **x86_64 Linux (glibc)**. Runtime requires glibc + libdbus (Secret
Service); headless VMs without a keyring daemon use the `~/.arrive` token file
fallback (mode `0600`).
