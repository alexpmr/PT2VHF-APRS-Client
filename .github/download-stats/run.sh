#!/usr/bin/env bash
# Atualiza o contador acumulado de downloads no ramo `badges` (lido pelos selos do README).
set -euo pipefail
git fetch -q origin badges || true
rm -rf .badges
if git rev-parse --verify -q origin/badges >/dev/null; then
  git worktree add -q .badges origin/badges
  git -C .badges checkout -q -B badges
else
  git worktree add -q --detach .badges
  git -C .badges checkout -q --orphan badges
  git -C .badges rm -rfq .
fi
python .github/download-stats/stats.py .badges/downloads
cd .badges
git add downloads
if git diff --cached --quiet; then echo "sem mudanças"; exit 0; fi
git -c user.name="github-actions[bot]" -c user.email="41898282+github-actions[bot]@users.noreply.github.com" \
  commit -qm "Contador de downloads [skip ci]"
git push -q origin badges
