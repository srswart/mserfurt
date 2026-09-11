#!/usr/bin/env bash
#
# Install the git-tracked ARRIVE CLI on an x86_64 Linux (glibc) machine.
#
# Verifies the checksum of the tarball committed under dist-public/linux/,
# extracts it, and runs the bundled install-from-tarball.sh so that:
#   - arrive     -> ~/.local/bin/arrive (or --dir DIR)
#   - templates  -> ~/.arrive/templates
#
# Intended for Cursor Cloud agent environment setup and other offline Linux VMs.
#
# Usage:
#   ./scripts/install-arrive-cli.sh
#   ./scripts/install-arrive-cli.sh --dir ~/.cargo/bin
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$REPO_ROOT/dist-public/linux"

INSTALL_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dir)
      INSTALL_ARGS+=(--dir "${2:?--dir requires a path}")
      shift 2
      ;;
    --prefix)
      INSTALL_ARGS+=(--prefix "${2:?--prefix requires a path}")
      shift 2
      ;;
    -h|--help)
      tail -n +2 "${BASH_SOURCE[0]}" | grep '^#' | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

TARBALL="$(ls "$DIST_DIR"/arrive-cli-v*-linux-x86_64.tar.gz 2>/dev/null | sort | tail -n1 || true)"
if [[ -z "$TARBALL" || ! -f "$TARBALL" ]]; then
  echo "Error: no arrive-cli-v*-linux-x86_64.tar.gz found in $DIST_DIR" >&2
  exit 1
fi

echo "Using tarball: $TARBALL"

if [[ -f "$DIST_DIR/SHA256SUMS" ]]; then
  echo "Verifying checksum..."
  (cd "$DIST_DIR" && sha256sum -c SHA256SUMS)
else
  echo "Warning: $DIST_DIR/SHA256SUMS not found; skipping checksum verification" >&2
fi

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

tar -xzf "$TARBALL" -C "$WORKDIR"
"$WORKDIR/install-from-tarball.sh" "${INSTALL_ARGS[@]}"
