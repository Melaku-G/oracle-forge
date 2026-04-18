#!/usr/bin/env bash
# Backwards-compatible wrapper: only GITHUB_REPOS.
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/load_datasets_from_dab.sh" GITHUB_REPOS "$@"
