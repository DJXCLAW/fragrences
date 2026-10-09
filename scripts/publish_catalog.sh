#!/usr/bin/env bash
# Run only in an ephemeral Actions checkout, NEVER in a user's working copy.
set -euo pipefail
if [ "${GITHUB_ACTIONS:-}" != "true" ]; then
  echo "This publisher runs only in GitHub Actions. Use the Python scripts for a local build." >&2
  exit 1
fi
git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
for attempt in 1 2 3; do
  # Rebuild against the latest main instead of merging generated JSON/HTML.
  # This reset affects only the disposable runner, not the remote or user files.
  git fetch origin main
  git reset --hard origin/main
  python -m unittest discover -s scripts -p 'test_catalog.py'
  python scripts/sync_brand_catalog.py
  python scripts/integrate_catalog.py
  node verify.cjs
  git add brand-catalog.js brand-catalog.json index.html
  if git diff --cached --quiet; then
    echo "Catalog and site are current."
    exit 0
  fi
  git commit -m "Refresh fragrance catalogs and integrate the site"
  if git push origin HEAD:main; then
    echo "Catalog and website committed successfully."
    exit 0
  fi
  echo "Main changed during the run; rebuilding on its latest commit (attempt $attempt/3)."
  sleep 2
done
echo "Could not publish after three attempts; remote history was not overwritten." >&2
exit 1
